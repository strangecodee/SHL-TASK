from scraper import SHLCatalogScraper
from data_processor import DataProcessor
from embeddings import EmbeddingGenerator
from config import Config
import os

def setup_system():
    print("=" * 60)
    print("SHL Assessment Recommendation System - Setup")
    print("=" * 60)
    
    # Create data directory if not exists
    if not os.path.exists(Config.DATA_DIR):
        os.makedirs(Config.DATA_DIR)
        print(f"Created data directory: {Config.DATA_DIR}")
    
    # Step 1: Scrape catalog
    print("\n[1/5] Scraping SHL catalog...")
    scraper = SHLCatalogScraper()
    catalog_df = scraper.scrape_catalog()
    scraper.save_catalog(catalog_df, Config.CATALOG_FILE)
    
    # Step 2: Normalize data
    print("\n[2/5] Normalizing catalog data...")
    processor = DataProcessor()
    catalog_df = processor.load_catalog()
    catalog_df = processor.normalize_data(catalog_df)
    processor.save_normalized_catalog(catalog_df)
    
    # Step 3: Generate embeddings
    print("\n[3/5] Generating embeddings...")
    embedder = EmbeddingGenerator()
    embeddings = embedder.generate_catalog_embeddings(catalog_df)
    embedder.save_embeddings(embeddings)
    
    # Step 4: Create sample training data
    print("\n[4/5] Creating sample training data...")
    processor.create_sample_train_data()
    
    # Step 5: Create sample test data
    print("\n[5/5] Creating sample test data...")
    processor.create_sample_test_data()
    
    print("\n" + "=" * 60)
    print("Setup completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Copy .env.example to .env and add your Gemini API key (optional)")
    print("2. Run 'python app.py' to start the API server")
    print("3. Run 'python evaluator.py' to evaluate the system")
    print("4. Run 'python csv_generator.py' to generate recommendations CSV")
    print("=" * 60)

if __name__ == "__main__":
    setup_system()
