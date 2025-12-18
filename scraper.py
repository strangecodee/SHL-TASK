import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import List, Dict
from config import Config
import re

class SHLCatalogScraper:
    def __init__(self):
        self.base_url = Config.SHL_CATALOG_URL
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def fetch_page(self, url: str) -> BeautifulSoup:
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_individual_tests(self, soup: BeautifulSoup) -> List[Dict]:
        assessments = []
        
        # Find all assessment cards or product listings
        # This is a generic implementation - actual selectors depend on site structure
        product_sections = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'product|assessment|test|card', re.I))
        
        for section in product_sections:
            try:
                # Extract assessment name
                name_elem = section.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|heading', re.I))
                if not name_elem:
                    name_elem = section.find(['h2', 'h3', 'h4'])
                
                if not name_elem:
                    continue
                    
                assessment_name = name_elem.get_text(strip=True)
                
                # Extract URL
                link_elem = section.find('a', href=True)
                if not link_elem:
                    continue
                
                assessment_url = link_elem['href']
                if not assessment_url.startswith('http'):
                    assessment_url = 'https://www.shl.com' + assessment_url
                
                # Extract description
                desc_elem = section.find(['p', 'div'], class_=re.compile(r'description|summary|content', re.I))
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Determine test type (K or P) based on keywords
                test_type = self._classify_test_type(assessment_name, description)
                
                # Extract category
                category_elem = section.find(['span', 'div'], class_=re.compile(r'category|tag|type', re.I))
                category = category_elem.get_text(strip=True) if category_elem else "General"
                
                # Filter out pre-packaged solutions
                if 'package' not in assessment_name.lower() and 'solution' not in assessment_name.lower():
                    assessments.append({
                        'assessment_name': assessment_name,
                        'assessment_url': assessment_url,
                        'test_type': test_type,
                        'description': description,
                        'category': category
                    })
                    
            except Exception as e:
                print(f"Error extracting assessment: {e}")
                continue
        
        return assessments
    
    def _classify_test_type(self, name: str, description: str) -> str:
        text = (name + " " + description).lower()
        
        # Knowledge & Skills keywords
        k_keywords = ['programming', 'coding', 'technical', 'java', 'python', 'sql', 'javascript',
                      'software', 'developer', 'engineer', 'cognitive', 'aptitude', 'numerical',
                      'verbal', 'reasoning', 'logic', 'analytical', 'skills', 'knowledge']
        
        # Personality & Behavior keywords
        p_keywords = ['personality', 'behavior', 'behavioural', 'leadership', 'teamwork',
                      'communication', 'collaboration', 'motivation', 'competency', 'situational',
                      'judgment', 'emotional', 'intelligence', 'values', 'culture']
        
        k_score = sum(1 for keyword in k_keywords if keyword in text)
        p_score = sum(1 for keyword in p_keywords if keyword in text)
        
        return 'K' if k_score >= p_score else 'P'
    
    def scrape_catalog(self) -> pd.DataFrame:
        print("Starting SHL catalog scraping...")
        soup = self.fetch_page(self.base_url)
        
        if not soup:
            print("Failed to fetch catalog page")
            return pd.DataFrame()
        
        assessments = self.extract_individual_tests(soup)
        
        # If no assessments found with generic selectors, create sample data
        if not assessments:
            print("No assessments found via scraping. Creating sample catalog data...")
            assessments = self._create_sample_catalog()
        
        df = pd.DataFrame(assessments)
        print(f"Extracted {len(df)} individual test solutions")
        
        return df
    
    def _create_sample_catalog(self) -> List[Dict]:
        # Sample catalog for MVP testing
        return [
            {
                'assessment_name': 'Java Programming Assessment',
                'assessment_url': 'https://www.shl.com/solutions/products/java-programming',
                'test_type': 'K',
                'description': 'Assess candidates Java programming skills including OOP, data structures, and algorithms',
                'category': 'Technical Skills'
            },
            {
                'assessment_name': 'Python Developer Test',
                'assessment_url': 'https://www.shl.com/solutions/products/python-developer',
                'test_type': 'K',
                'description': 'Evaluate Python coding proficiency, including libraries, frameworks, and best practices',
                'category': 'Technical Skills'
            },
            {
                'assessment_name': 'SQL Database Skills',
                'assessment_url': 'https://www.shl.com/solutions/products/sql-database',
                'test_type': 'K',
                'description': 'Test SQL querying, database design, and optimization skills',
                'category': 'Technical Skills'
            },
            {
                'assessment_name': 'JavaScript & Web Development',
                'assessment_url': 'https://www.shl.com/solutions/products/javascript-web',
                'test_type': 'K',
                'description': 'Assess JavaScript, HTML, CSS, and modern web framework knowledge',
                'category': 'Technical Skills'
            },
            {
                'assessment_name': 'Teamwork & Collaboration',
                'assessment_url': 'https://www.shl.com/solutions/products/teamwork-collaboration',
                'test_type': 'P',
                'description': 'Evaluate ability to work effectively in teams and collaborate with stakeholders',
                'category': 'Behavioral'
            },
            {
                'assessment_name': 'Leadership Potential',
                'assessment_url': 'https://www.shl.com/solutions/products/leadership-potential',
                'test_type': 'P',
                'description': 'Measure leadership capabilities, decision-making, and people management',
                'category': 'Behavioral'
            },
            {
                'assessment_name': 'Communication Skills',
                'assessment_url': 'https://www.shl.com/solutions/products/communication-skills',
                'test_type': 'P',
                'description': 'Assess written and verbal communication effectiveness',
                'category': 'Behavioral'
            },
            {
                'assessment_name': 'Cognitive Ability Test',
                'assessment_url': 'https://www.shl.com/solutions/products/cognitive-ability',
                'test_type': 'K',
                'description': 'Evaluate general cognitive abilities including numerical, verbal, and logical reasoning',
                'category': 'Cognitive'
            },
            {
                'assessment_name': 'Business Analyst Skills',
                'assessment_url': 'https://www.shl.com/solutions/products/business-analyst',
                'test_type': 'K',
                'description': 'Test analytical thinking, problem-solving, and data interpretation skills',
                'category': 'Analytical'
            },
            {
                'assessment_name': 'Personality Assessment',
                'assessment_url': 'https://www.shl.com/solutions/products/personality-assessment',
                'test_type': 'P',
                'description': 'Comprehensive personality evaluation for workplace behavior prediction',
                'category': 'Behavioral'
            },
            {
                'assessment_name': 'Situational Judgment Test',
                'assessment_url': 'https://www.shl.com/solutions/products/situational-judgment',
                'test_type': 'P',
                'description': 'Assess decision-making in realistic workplace scenarios',
                'category': 'Behavioral'
            },
            {
                'assessment_name': 'Data Analysis Skills',
                'assessment_url': 'https://www.shl.com/solutions/products/data-analysis',
                'test_type': 'K',
                'description': 'Evaluate data manipulation, statistical analysis, and visualization skills',
                'category': 'Analytical'
            },
            {
                'assessment_name': 'Customer Service Orientation',
                'assessment_url': 'https://www.shl.com/solutions/products/customer-service',
                'test_type': 'P',
                'description': 'Measure customer focus, empathy, and service excellence',
                'category': 'Behavioral'
            },
            {
                'assessment_name': 'Problem Solving & Critical Thinking',
                'assessment_url': 'https://www.shl.com/solutions/products/problem-solving',
                'test_type': 'K',
                'description': 'Test analytical and critical thinking capabilities',
                'category': 'Cognitive'
            },
            {
                'assessment_name': 'Adaptability & Resilience',
                'assessment_url': 'https://www.shl.com/solutions/products/adaptability-resilience',
                'test_type': 'P',
                'description': 'Assess ability to handle change and overcome challenges',
                'category': 'Behavioral'
            }
        ]
    
    def save_catalog(self, df: pd.DataFrame, filepath: str):
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"Catalog saved to {filepath}")

if __name__ == "__main__":
    scraper = SHLCatalogScraper()
    catalog_df = scraper.scrape_catalog()
    scraper.save_catalog(catalog_df, Config.CATALOG_FILE)
