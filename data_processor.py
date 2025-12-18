import pandas as pd
import numpy as np
from typing import List, Dict
from config import Config

class DataProcessor:
    def __init__(self):
        self.catalog_df = None
        
    def load_catalog(self, filepath: str = None) -> pd.DataFrame:
        if filepath is None:
            filepath = Config.CATALOG_FILE
        
        try:
            self.catalog_df = pd.read_csv(filepath)
            print(f"Loaded {len(self.catalog_df)} assessments from catalog")
            return self.catalog_df
        except FileNotFoundError:
            print(f"Catalog file not found at {filepath}")
            return pd.DataFrame()
    
    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Remove duplicates
        df = df.drop_duplicates(subset=['assessment_url'])
        
        # Clean text fields
        df['assessment_name'] = df['assessment_name'].str.strip()
        df['description'] = df['description'].fillna('').str.strip()
        df['category'] = df['category'].fillna('General').str.strip()
        
        # Validate test_type
        df['test_type'] = df['test_type'].apply(lambda x: x if x in ['K', 'P'] else 'K')
        
        # Create combined text for embedding
        df['combined_text'] = df.apply(
            lambda row: f"{row['assessment_name']} {row['category']} {row['description']}", 
            axis=1
        )
        
        return df
    
    def save_normalized_catalog(self, df: pd.DataFrame, filepath: str = None):
        if filepath is None:
            filepath = Config.CATALOG_FILE
        
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"Normalized catalog saved to {filepath}")
    
    def load_train_data(self, filepath: str = None) -> pd.DataFrame:
        if filepath is None:
            # Prefer official Gen_AI Dataset.xlsx if present
            try:
                df = pd.read_excel(
                    Config.GEN_AI_DATASET_FILE,
                    sheet_name=Config.TRAIN_SHEET_NAME
                )
                # Map Excel columns to internal schema
                # Query -> query, Assessment_url -> relevant_urls
                rename_map = {}
                if 'Query' in df.columns:
                    rename_map['Query'] = 'query'
                if 'Assessment_url' in df.columns:
                    rename_map['Assessment_url'] = 'relevant_urls'
                if rename_map:
                    df = df.rename(columns=rename_map)
                print(f"Loaded {len(df)} training queries from Excel")
                return df
            except FileNotFoundError:
                print(f"Excel training data not found at {Config.GEN_AI_DATASET_FILE}, sheet {Config.TRAIN_SHEET_NAME}")
            except ValueError as e:
                print(f"Error loading Excel training sheet: {e}")
        
        # Fallback to CSV if Excel is missing or invalid
        if filepath is None:
            filepath = Config.TRAIN_DATA_FILE
        
        try:
            train_df = pd.read_csv(filepath)
            print(f"Loaded {len(train_df)} training queries from {filepath}")
            return train_df
        except FileNotFoundError:
            print(f"Training data not found at {filepath}")
            return pd.DataFrame()
    
    def load_test_data(self, filepath: str = None) -> pd.DataFrame:
        if filepath is None:
            # Prefer official Gen_AI Dataset.xlsx if present
            try:
                df = pd.read_excel(
                    Config.GEN_AI_DATASET_FILE,
                    sheet_name=Config.TEST_SHEET_NAME
                )
                # Map Excel column to internal schema
                if 'Query' in df.columns:
                    df = df.rename(columns={'Query': 'query'})
                print(f"Loaded {len(df)} test queries from Excel")
                return df
            except FileNotFoundError:
                print(f"Excel test data not found at {Config.GEN_AI_DATASET_FILE}, sheet {Config.TEST_SHEET_NAME}")
            except ValueError as e:
                print(f"Error loading Excel test sheet: {e}")
        
        # Fallback to CSV if Excel is missing or invalid
        if filepath is None:
            filepath = Config.TEST_DATA_FILE
        
        try:
            test_df = pd.read_csv(filepath)
            print(f"Loaded {len(test_df)} test queries from {filepath}")
            return test_df
        except FileNotFoundError:
            print(f"Test data not found at {filepath}")
            return pd.DataFrame()
    
    def create_sample_train_data(self):
        # Sample training data for testing
        sample_queries = [
            {
                'query': 'I am hiring for Java developers who can collaborate with business teams',
                'relevant_urls': 'https://www.shl.com/solutions/products/java-programming;https://www.shl.com/solutions/products/teamwork-collaboration;https://www.shl.com/solutions/products/communication-skills'
            },
            {
                'query': 'Need an analyst screening solution using cognitive and personality tests',
                'relevant_urls': 'https://www.shl.com/solutions/products/cognitive-ability;https://www.shl.com/solutions/products/business-analyst;https://www.shl.com/solutions/products/personality-assessment'
            },
            {
                'query': 'Looking to hire professionals skilled in Python, SQL, and JavaScript',
                'relevant_urls': 'https://www.shl.com/solutions/products/python-developer;https://www.shl.com/solutions/products/sql-database;https://www.shl.com/solutions/products/javascript-web'
            }
        ]
        
        df = pd.DataFrame(sample_queries)
        df.to_csv(Config.TRAIN_DATA_FILE, index=False)
        print(f"Sample training data created at {Config.TRAIN_DATA_FILE}")
        return df
    
    def create_sample_test_data(self):
        # Sample test data for testing
        sample_queries = [
            {'query': 'Hiring software engineers with strong problem-solving skills'},
            {'query': 'Need customer service representatives with excellent communication'},
            {'query': 'Looking for data analysts proficient in statistical analysis'}
        ]
        
        df = pd.DataFrame(sample_queries)
        df.to_csv(Config.TEST_DATA_FILE, index=False)
        print(f"Sample test data created at {Config.TEST_DATA_FILE}")
        return df

if __name__ == "__main__":
    processor = DataProcessor()
    
    # Load and normalize catalog
    catalog = processor.load_catalog()
    if not catalog.empty:
        normalized = processor.normalize_data(catalog)
        processor.save_normalized_catalog(normalized)
    
    # Create sample data if needed
    processor.create_sample_train_data()
    processor.create_sample_test_data()
