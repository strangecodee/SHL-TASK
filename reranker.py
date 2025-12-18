import google.generativeai as genai
from typing import List, Dict
from config import Config
import json
import re

class GenAIReranker:
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = Config.GEMINI_API_KEY
        
        if not api_key:
            print("Warning: No Gemini API key provided. Re-ranking will use rule-based fallback.")
            self.use_llm = False
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.use_llm = True
    
    def analyze_query_domain(self, query: str) -> str:
        query_lower = query.lower()
        
        # Technical / knowledge-oriented keywords
        technical_keywords = [
            # Roles / functions
            'developer', 'engineer', 'tester', 'qa', 'sdet',
            'analyst', 'analysts', 'data scientist', 'scientist',
            'programmer', 'architect',
            # Skills / technologies
            'programming', 'coding', 'java', 'python', 'c++', 'c#',
            'javascript', 'typescript', 'sql', 'nosql', 'database',
            'react', 'angular', 'node', 'dotnet', '.net', 'spring',
            'frontend', 'front-end', 'backend', 'back-end',
            'full stack', 'cloud', 'aws', 'azure', 'gcp',
            'linux', 'devops', 'automation',
            # Cognitive / aptitude
            'cognitive', 'aptitude', 'numerical', 'verbal',
            'reasoning', 'logical', 'logic', 'problem solving',
            'quantitative', 'statistics', 'statistical',
            # Tools
            'excel', 'power bi', 'tableau', 'sql server'
        ]
        
        # Behavioral / personality-oriented keywords
        behavioral_keywords = [
            # Interpersonal / communication
            'collaborate', 'collaboration', 'teamwork', 'team player',
            'communication', 'communicator', 'presentation',
            'stakeholder', 'client', 'customer', 'service', 'support',
            'relationship', 'negotiation', 'influence',
            # Leadership / management
            'leadership', 'leader', 'manage', 'management',
            'people manager', 'coaching', 'mentoring',
            # Traits / soft skills
            'adaptability', 'flexibility', 'resilience', 'stress',
            'pressure', 'conflict', 'empathy', 'trust',
            'initiative', 'ownership', 'proactive', 'motivation',
            'drive', 'values', 'culture', 'fit',
            # Assessment-related
            'personality', 'behavior', 'behavioural',
            'situational', 'judgment', 'sjt', 'emotional', 'eq',
            'work style', 'competency', 'competencies'
        ]
        
        tech_score = sum(1 for kw in technical_keywords if kw in query_lower)
        behav_score = sum(1 for kw in behavioral_keywords if kw in query_lower)
        
        # Require a clear margin; otherwise treat as mixed
        if tech_score >= behav_score + 2:
            return 'technical'
        elif behav_score >= tech_score + 2:
            return 'behavioral'
        else:
            return 'mixed'
    
    def balance_recommendations(self, candidates: List[Dict], query: str, 
                               final_count: int = None) -> List[Dict]:
        if final_count is None:
            final_count = Config.FINAL_RECOMMENDATIONS
        
        # Separate K and P type assessments
        k_assessments = [c for c in candidates if c['test_type'] == 'K']
        p_assessments = [c for c in candidates if c['test_type'] == 'P']
        
        # Fixed split: 70% K, 30% P
        k_count = min(int(final_count * 0.7), len(k_assessments))
        p_count = min(final_count - k_count, len(p_assessments))
        
        # Adjust if we don't have enough P
        if k_count + p_count < final_count:
            k_count = min(final_count - p_count, len(k_assessments))
        
        # Select balanced recommendations
        balanced = []
        balanced.extend(k_assessments[:k_count])
        balanced.extend(p_assessments[:p_count])
        
        # Fill remaining slots
        remaining = final_count - len(balanced)
        if remaining > 0:
            # Add from K if available
            k_remaining = k_assessments[k_count:k_count + remaining]
            balanced.extend(k_remaining)
            remaining -= len(k_remaining)
            
            # Add from P if still needed
            if remaining > 0:
                p_remaining = p_assessments[p_count:p_count + remaining]
                balanced.extend(p_remaining)
        
        return balanced[:final_count]
    
    def rerank_with_llm(self, query: str, candidates: List[Dict], 
                        final_count: int = None) -> List[Dict]:
        if not self.use_llm:
            print("LLM not available, using rule-based balancing")
            return self.balance_recommendations(candidates, query, final_count)
        
        if final_count is None:
            final_count = Config.FINAL_RECOMMENDATIONS
        
        try:
            # Create prompt for LLM
            prompt = self._create_reranking_prompt(query, candidates, final_count)
            
            # Get LLM response
            response = self.model.generate_content(prompt)
            
            # Parse response
            reranked = self._parse_llm_response(response.text, candidates)
            
            # Apply balancing to LLM results
            return self.balance_recommendations(reranked, query, final_count)
            
        except Exception as e:
            print(f"LLM re-ranking failed: {e}. Using rule-based fallback.")
            return self.balance_recommendations(candidates, query, final_count)
    
    def _create_reranking_prompt(self, query: str, candidates: List[Dict], 
                                final_count: int) -> str:
        candidates_text = ""
        for i, candidate in enumerate(candidates):
            candidates_text += f"{i+1}. {candidate['assessment_name']} ({candidate['test_type']})\n"
            candidates_text += f"   Category: {candidate['category']}\n"
            candidates_text += f"   Description: {candidate['description']}\n\n"
        
        prompt = f"""You are an expert HR assessment advisor. Given a hiring query and a list of candidate assessments, 
rank the assessments by relevance to the query.

Query: {query}

Candidate Assessments:
{candidates_text}

Instructions:
1. Analyze the query to understand required skills and competencies
2. Rank assessments by relevance (most relevant first)
3. Consider both technical (K-type) and behavioral (P-type) assessments
4. Return the top {final_count} most relevant assessment numbers

Return ONLY a JSON array of assessment numbers in order of relevance.
Example format: [3, 1, 7, 2, 5, 9, 4, 6, 8, 10]
"""
        return prompt
    
    def _parse_llm_response(self, response_text: str, candidates: List[Dict]) -> List[Dict]:
        try:
            # Extract JSON array from response
            match = re.search(r'\[[\d,\s]+\]', response_text)
            if match:
                indices = json.loads(match.group())
                reranked = []
                for idx in indices:
                    if 1 <= idx <= len(candidates):
                        reranked.append(candidates[idx - 1])
                return reranked
            else:
                print("Could not parse LLM response, returning original order")
                return candidates
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return candidates
    
    def recommend(self, query: str, candidates: List[Dict], 
                  final_count: int = None) -> List[Dict]:
        if self.use_llm:
            return self.rerank_with_llm(query, candidates, final_count)
        else:
            return self.balance_recommendations(candidates, query, final_count)

if __name__ == "__main__":
    print("Reranker module - no standalone execution")
