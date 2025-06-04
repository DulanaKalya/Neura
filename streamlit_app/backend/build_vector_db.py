"""
Enhanced script to build emergency knowledge vector database from PDFs
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.vector_db import EmergencyKnowledgeVectorDB
import argparse

def main():
    parser = argparse.ArgumentParser(description='Build Emergency Knowledge Vector Database')
    parser.add_argument('--force', action='store_true', help='Force rebuild even if PDFs haven\'t changed')
    parser.add_argument('--pdf-path', default='./data/pdfs', help='Path to PDF files directory')
    args = parser.parse_args()
    
    print("Building Emergency Knowledge Vector Database from PDFs...")
    
    # Initialize database
    db = EmergencyKnowledgeVectorDB(
        local_storage_path="./data/vector_db",
        pdf_path=args.pdf_path
    )
    
    # Check PDF status
    pdf_status = db.get_pdf_status()
    print(f"\nPDF Directory: {pdf_status['pdf_directory']}")
    print(f"PDF Files Found: {pdf_status['pdf_count']}")
    
    if pdf_status['pdf_files']:
        print("PDFs to process:")
        for pdf in pdf_status['pdf_files']:
            print(f"  - {pdf}")
    else:
        print("⚠️  No PDF files found. Please add PDF files to the pdfs folder.")
        print("   The system will use fallback documents for now.")
    
    # Build vector database
    print("\nProcessing documents and creating embeddings...")
    success = db.build_vector_database(force_rebuild=args.force)
    
    if not success:
        print("❌ Failed to build vector database")
        return
    
    # Save to local storage
    print("\nSaving to local storage...")
    save_success = db.save_locally()
    
    if save_success:
        print("✅ Emergency knowledge database built and saved successfully!")
        print(f"Database contains {len(db.documents)} document chunks")
        
        # Show source breakdown
        info = db.get_database_info()
        if info and 'source_breakdown' in info:
            print("\nSource breakdown:")
            for source, count in info['source_breakdown'].items():
                print(f"  - {source}: {count} chunks")
    else:
        print("❌ Failed to save database to local storage")
    
    # Test search functionality
    print("\n🔍 Testing search functionality:")
    test_queries = [
        "what to do during earthquake",
        "flood safety",
        "hurricane evacuation",
        "first aid bleeding"
    ]
    
    for query in test_queries:
        results = db.search(query, k=2)
        print(f"\nQuery: '{query}'")
        for doc, score in results:
            source = doc.get('source', 'unknown')
            print(f"  - {doc['title'][:50]}... (Source: {source}, Score: {score:.3f})")

if __name__ == "__main__":
    main()