import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict, Tuple
import pickle
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
import hashlib
from pathlib import Path
import glob

class EmergencyKnowledgeVectorDB:
    def __init__(self, model_name="all-MiniLM-L6-v2", local_storage_path="./data/vector_db", pdf_path="./data/pdfs"):
        """
        Initialize the vector database for emergency knowledge with local storage
        """
        self.model = SentenceTransformer(model_name)
        self.documents = []
        self.embeddings = None
        self.index = None
        self.storage_path = local_storage_path
        self.pdf_path = pdf_path
        
        # Create storage directories if they don't exist
        os.makedirs(self.storage_path, exist_ok=True)
        os.makedirs(self.pdf_path, exist_ok=True)
        
        # Define file paths
        self.documents_path = os.path.join(self.storage_path, "documents.pkl")
        self.embeddings_path = os.path.join(self.storage_path, "embeddings.npy")
        self.index_path = os.path.join(self.storage_path, "faiss_index.index")
        self.metadata_path = os.path.join(self.storage_path, "metadata.json")
        self.pdf_hashes_path = os.path.join(self.storage_path, "pdf_hashes.json")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
        self.emergency_categories = {
            "earthquake": {
                "name": "Earthquake Safety",
                "description": "Earthquake preparedness, response during seismic activity, drop cover hold procedures, aftershock safety, building damage assessment, post-earthquake recovery, seismic hazards, ground shaking, structural collapse prevention",
                "keywords": ["earthquake", "seismic", "tremor", "quake", "ground shaking", "aftershock", "drop cover hold", "building collapse"]
            },
            "flood": {
                "name": "Flood Response",
                "description": "Flood safety procedures, water evacuation, flash flood response, driving in flooded areas, water damage cleanup, flood preparedness, rising water levels, water rescue, turn around don't drown",
                "keywords": ["flood", "water", "inundation", "overflow", "flash flood", "rising water", "evacuate", "turn around don't drown"]
            },
            "hurricane": {
                "name": "Hurricane & Storm Safety",
                "description": "Hurricane preparedness, tropical storm safety, high wind protection, storm surge evacuation, hurricane eye safety, boarding windows, evacuation routes, shelter procedures, typhoon cyclone response",
                "keywords": ["hurricane", "typhoon", "cyclone", "storm", "wind", "storm surge", "evacuation", "shelter", "tropical storm"]
            },
            "wildfire": {
                "name": "Wildfire Emergency",
                "description": "Wildfire evacuation procedures, fire safety, smoke protection, defensible space, fire-resistant landscaping, escape routes, firefighting, forest fire, brush fire, fire shelter",
                "keywords": ["wildfire", "fire", "forest fire", "brush fire", "evacuation", "smoke", "defensible space", "fire safety"]
            },
            "tornado": {
                "name": "Tornado Safety",
                "description": "Tornado shelter procedures, severe weather response, basement safety, mobile home evacuation, tornado warning signs, safe rooms, storm cellars, debris protection, severe thunderstorms",
                "keywords": ["tornado", "twister", "severe weather", "shelter", "basement", "safe room", "storm cellar", "debris"]
            },
            "first_aid": {
                "name": "Medical Emergency & First Aid",
                "description": "First aid procedures, medical emergency response, bleeding control, shock treatment, CPR, wound care, emergency medical treatment, injury assessment, life-saving techniques, medical supplies",
                "keywords": ["first aid", "medical", "bleeding", "wound", "injury", "CPR", "shock", "emergency treatment", "medical supplies"]
            },
            "communication": {
                "name": "Emergency Communication",
                "description": "Emergency communication systems, radio procedures, emergency contacts, alert systems, communication during disasters, emergency broadcasting, family communication plans, emergency signals",
                "keywords": ["communication", "radio", "emergency contact", "alert", "broadcasting", "signals", "family plan"]
            },
            "evacuation": {
                "name": "Evacuation Procedures",
                "description": "Evacuation planning, escape routes, shelter procedures, emergency exits, transportation during emergencies, evacuation orders, safe zones, temporary shelters, relocation procedures",
                "keywords": ["evacuation", "escape", "exit", "shelter", "safe zone", "relocation", "emergency transport"]
            },
            "water_safety": {
                "name": "Water Safety & Purification",
                "description": "Water purification methods, emergency water sources, water safety during disasters, drinking water contamination, water storage, water treatment, waterborne diseases, emergency hydration",
                "keywords": ["water purification", "drinking water", "water safety", "contamination", "water storage", "emergency water"]
            },
            "sri_lanka_specific": {
                "name": "Sri Lanka Emergency Response",
                "description": "Sri Lanka specific emergency procedures, monsoon safety, landslide warnings, tsunami response, local emergency services, tropical climate disasters, regional emergency protocols, local hazards",
                "keywords": ["sri lanka", "monsoon", "landslide", "tsunami", "tropical", "local emergency", "regional hazards"]
            }
        }
        
        self.category_similarity_threshold = 0.3
        self.content_relevance_threshold = 0.20


    def initialize_with_fallback(self):
        """
        Initialize the database with proper fallback handling
        """
        try:
            # Try to load existing database first
            if self.load_locally():
                print("✅ Loaded existing database from local storage")
                return True
            
            print("📂 No existing database found, building new one...")
            
            # If no existing database, try to build from PDFs
            success = self.build_vector_database()
            if success:
                self.save_locally()
                print("✅ Built and saved new database successfully")
                return True
            
            # If both fail, use hardcoded documents
            print("⚠️ PDF processing failed, falling back to hardcoded emergency documents")
            fallback_docs = self.create_emergency_knowledge_base()
            success = self.build_vector_database(documents=fallback_docs)
            
            if success:
                self.save_locally()
                print("✅ Built database with fallback documents")
                return True
            else:
                print("❌ Failed to build database even with fallback documents")
                return False
            
        except Exception as e:
            print(f"❌ Error in initialize_with_fallback: {str(e)}")
            return False


    def get_category_embeddings(self):
        """
        Create embeddings for category descriptions
        """
        if not hasattr(self, '_category_embeddings'):
            category_texts = [cat_info["description"] for cat_info in self.emergency_categories.values()]
            self._category_embeddings = self.model.encode(category_texts)
            faiss.normalize_L2(self._category_embeddings)
        return self._category_embeddings
    
    def determine_content_category(self, content: str) -> Tuple[str, float, bool]:
        """
        Determine the most appropriate category for content using semantic similarity
        Returns: (category, confidence_score, is_relevant)
        """
        try:
            # Encode the content
            content_embedding = self.model.encode([content])
            faiss.normalize_L2(content_embedding)
            
            # Get category embeddings
            category_embeddings = self.get_category_embeddings()
            
            # Calculate similarities
            similarities = np.dot(content_embedding, category_embeddings.T)[0]
            
            # Find best match
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            
            category_names = list(self.emergency_categories.keys())
            best_category = category_names[best_idx]
            
            # Check if content is relevant enough
            is_relevant = best_score >= self.content_relevance_threshold
            
            return best_category, float(best_score), is_relevant
            
        except Exception as e:
            print(f"Error determining category: {str(e)}")
            return "emergency_guide", 0.0, False


    def is_emergency_relevant_content(self, content: str) -> Tuple[bool, float]:
        """
        Check if content is relevant to emergency response at all
        """
        emergency_keywords = [
            "emergency", "disaster", "safety", "evacuation", "rescue", "first aid", 
            "fire", "flood", "earthquake", "storm", "hurricane", "tornado", "medical",
            "help", "danger", "warning", "prepare", "response", "survival", "shelter",
            "emergency kit", "emergency plan", "emergency supplies", "hazard", "risk"
        ]
        
        content_lower = content.lower()
        
        # Count emergency-related keywords
        keyword_matches = sum(1 for keyword in emergency_keywords if keyword in content_lower)
        
        # Calculate relevance score based on keyword density
        words = content_lower.split()
        if len(words) == 0:
            return False, 0.0
        
        relevance_score = keyword_matches / len(words) * 100  # Percentage of emergency keywords
        
        # Also use semantic similarity with general emergency description
        emergency_description = "emergency response disaster preparedness safety procedures evacuation first aid rescue operations"
        
        try:
            content_embedding = self.model.encode([content])
            emergency_embedding = self.model.encode([emergency_description])
            faiss.normalize_L2(content_embedding)
            faiss.normalize_L2(emergency_embedding)
            
            semantic_similarity = np.dot(content_embedding, emergency_embedding.T)[0][0]
            
            # Combine keyword and semantic scores
            combined_score = (relevance_score / 100 * 0.3) + (semantic_similarity * 0.7)
            
            is_relevant = combined_score >= self.content_relevance_threshold
            
            return is_relevant, float(combined_score)
            
        except:
            # Fallback to keyword-only assessment
            is_relevant = relevance_score >= 1.0  # At least 1% emergency keywords
            return is_relevant, relevance_score / 100



    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from a PDF file
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                
                return text.strip()
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""
    
    def get_file_hash(self, file_path: str) -> str:
        """
        Get MD5 hash of a file to detect changes
        """
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def load_pdf_hashes(self) -> Dict:
        """
        Load previously processed PDF file hashes
        """
        if os.path.exists(self.pdf_hashes_path):
            try:
                with open(self.pdf_hashes_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_pdf_hashes(self, hashes: Dict):
        """
        Save PDF file hashes to track changes
        """
        try:
            with open(self.pdf_hashes_path, 'w') as f:
                json.dump(hashes, f, indent=2)
        except Exception as e:
            print(f"Error saving PDF hashes: {str(e)}")
    
    def process_pdf_file(self, pdf_path: str, force_category: str = None) -> List[Dict]:
        """
        Process a single PDF file and create document chunks with category filtering
        """
        print(f"Processing PDF: {pdf_path}")
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print(f"No text extracted from {pdf_path}")
            return []
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create document objects with category filtering
        documents = []
        pdf_name = Path(pdf_path).stem
        processed_chunks = 0
        filtered_chunks = 0
        
        for i, chunk in enumerate(chunks):
            # Clean up the chunk
            chunk = chunk.strip()
            if len(chunk) < 50:  # Skip very short chunks
                continue
            
            processed_chunks += 1
            
            # Check if content is emergency-relevant
            is_relevant, relevance_score = self.is_emergency_relevant_content(chunk)
            
            if not is_relevant:
                filtered_chunks += 1
                print(f"  Filtered out irrelevant chunk {i+1}: {chunk[:100]}...")
                continue
            
            # Determine category
            if force_category and force_category in self.emergency_categories:
                category = force_category
                category_confidence = 1.0
            else:
                category, category_confidence, category_relevant = self.determine_content_category(chunk)
                
                if not category_relevant:
                    filtered_chunks += 1
                    print(f"  Filtered out low-confidence chunk {i+1}: confidence {category_confidence:.3f}")
                    continue
            
            # Create title from first line or use generic title
            lines = chunk.split('\n')
            title = lines[0][:100] if lines else f"{pdf_name} - Part {i+1}"
            title = title.strip().rstrip('.')
            
            doc = {
                "category": category,
                "title": title,
                "content": chunk,
                "source": pdf_name,
                "chunk_id": i,
                "file_path": pdf_path,
                "relevance_score": relevance_score,
                "category_confidence": category_confidence
            }
            documents.append(doc)
        
        print(f"Created {len(documents)} relevant chunks from {pdf_path}")
        print(f"  Processed: {processed_chunks} chunks, Filtered out: {filtered_chunks} chunks")
        
        return documents
    
    def process_all_pdfs(self, force_rebuild: bool = False) -> List[Dict]:
        """
        Process all PDF files in the PDF directory with better error handling
        """
        all_documents = []
        current_hashes = {}
        saved_hashes = self.load_pdf_hashes()
        
        # Find all PDF files
        pdf_files = glob.glob(os.path.join(self.pdf_path, "*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {self.pdf_path}")
            print("Using fallback hardcoded documents.")
            return self.create_emergency_knowledge_base()
        
        print(f"Found {len(pdf_files)} PDF files")
        processed_count = 0
        
        for pdf_path in pdf_files:
            try:
                file_hash = self.get_file_hash(pdf_path)
                current_hashes[pdf_path] = file_hash
                
                # Check if file has changed or force rebuild
                if force_rebuild or pdf_path not in saved_hashes or saved_hashes[pdf_path] != file_hash:
                    print(f"Processing new/changed file: {pdf_path}")
                    
                    # Process the PDF without forcing a category
                    # Let the content-based category determination decide
                    documents = self.process_pdf_file(pdf_path, force_category=None)
                    
                    if documents:  # Only add if we got valid documents
                        all_documents.extend(documents)
                        processed_count += 1
                        print(f"  ✅ Successfully processed {len(documents)} chunks from {os.path.basename(pdf_path)}")
                    else:
                        print(f"  ⚠️ Warning: No valid documents extracted from {pdf_path}")
                else:
                    print(f"Skipping unchanged file: {pdf_path}")
                    
            except Exception as e:
                print(f"❌ Error processing {pdf_path}: {str(e)}")
                continue
        
        # Save updated hashes
        self.save_pdf_hashes(current_hashes)
        
        print(f"\n📊 Processing Summary:")
        print(f"  Total PDF files found: {len(pdf_files)}")
        print(f"  Successfully processed: {processed_count} PDF files")
        print(f"  Total document chunks created: {len(all_documents)}")
        
        # If no documents were processed and we don't have existing ones, use fallback
        if not all_documents:
            print("\n⚠️ No new documents processed. Checking for existing documents...")
            if self.documents and len(self.documents) > 0:
                print(f"Using existing {len(self.documents)} documents")
                return self.documents
            else:
                print("No existing documents found. Using fallback hardcoded documents.")
                return self.create_emergency_knowledge_base()
        
        return all_documents
    
    def print_category_distribution(self):
        """
        Print distribution of documents across categories
        """
        if not self.documents:
            return
        
        category_counts = {}
        for doc in self.documents:
            category = doc.get('category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print("\nCategory Distribution:")
        for category, count in sorted(category_counts.items()):
            category_name = self.emergency_categories.get(category, {}).get('name', category)
            print(f"  {category_name}: {count} documents")
        
        # Print quality statistics
        if hasattr(self, 'documents') and self.documents:
            relevance_scores = [doc.get('relevance_score', 0) for doc in self.documents if 'relevance_score' in doc]
            category_confidences = [doc.get('category_confidence', 0) for doc in self.documents if 'category_confidence' in doc]
            
            if relevance_scores:
                avg_relevance = sum(relevance_scores) / len(relevance_scores)
                print(f"\nQuality Metrics:")
                print(f"  Average Relevance Score: {avg_relevance:.3f}")
            
            if category_confidences:
                avg_confidence = sum(category_confidences) / len(category_confidences)
                print(f"  Average Category Confidence: {avg_confidence:.3f}")

    def create_emergency_knowledge_base(self):
        """
        Create comprehensive fallback emergency knowledge base
        """
        emergency_documents = [
            # Earthquake Safety
            {
                "category": "earthquake",
                "title": "During Earthquake Safety",
                "content": "Drop, Cover, and Hold On. Drop to your hands and knees, take cover under a sturdy desk or table, and hold on to your shelter. If no table is available, cover your head and neck with your arms. Stay away from windows, mirrors, and heavy objects that could fall.",
                "source": "builtin",
                "chunk_id": 0
            },
            {
                "category": "earthquake",
                "title": "After Earthquake Safety",
                "content": "Check for injuries and provide first aid. Check for hazards like gas leaks, electrical damage, and structural damage. Do not use elevators. Be prepared for aftershocks. Stay out of damaged buildings.",
                "source": "builtin",
                "chunk_id": 1
            },
            
            # Flood Safety
            {
                "category": "flood",
                "title": "Flood Safety Rules",
                "content": "Never drive through flooded roads. Just 6 inches of moving water can knock you down, and 12 inches can carry away a vehicle. Turn Around, Don't Drown. Move to higher ground immediately.",
                "source": "builtin",
                "chunk_id": 2
            },
            {
                "category": "flood",
                "title": "Flash Flood Response",
                "content": "If caught in a flash flood while driving, abandon your vehicle immediately and move to higher ground. If trapped in a building, go to the highest floor but not the attic as you may become trapped by rising water.",
                "source": "builtin",
                "chunk_id": 3
            },
            
            # First Aid
            {
                "category": "first_aid",
                "title": "Severe Bleeding Control",
                "content": "Apply direct pressure to the wound with a clean cloth. If blood soaks through, add more layers without removing the first. Elevate the injured area above the heart if possible. Apply pressure to pressure points if bleeding doesn't stop.",
                "source": "builtin",
                "chunk_id": 4
            },
            {
                "category": "first_aid",
                "title": "Shock Treatment",
                "content": "Have the person lie down with feet elevated 8-12 inches unless head, neck, or back injury is suspected. Keep person warm with blankets. Do not give food or water. Monitor breathing and pulse. Get medical help immediately.",
                "source": "builtin",
                "chunk_id": 5
            },
            
            # Hurricane Safety
            {
                "category": "hurricane",
                "title": "Hurricane Evacuation",
                "content": "Evacuate immediately if ordered by authorities. Follow designated evacuation routes. Do not take shortcuts as they may be blocked. If you cannot evacuate, find a safe room away from windows on the lowest floor of a sturdy building.",
                "source": "builtin",
                "chunk_id": 6
            },
            
            # Wildfire Safety
            {
                "category": "wildfire",
                "title": "Wildfire Evacuation",
                "content": "Evacuate early when advised. Have multiple escape routes planned. Keep your vehicle fueled and ready. If trapped by wildfire, call 911 and find a body of water or cleared area. Lie face down and cover yourself with wet clothing or soil.",
                "source": "builtin",
                "chunk_id": 7
            },
            
            # Sri Lanka Specific
            {
                "category": "sri_lanka_specific",
                "title": "Monsoon Safety Sri Lanka",
                "content": "During monsoon season in Sri Lanka, avoid traveling through flood-prone areas like Kelani Valley and Gampaha. Monitor weather alerts from the Department of Meteorology. Prepare for power outages by keeping charged devices and backup power sources.",
                "source": "builtin",
                "chunk_id": 8
            },
            {
                "category": "sri_lanka_specific",
                "title": "Landslide Warning Signs Sri Lanka",
                "content": "In hilly areas like Kandy, Nuwara Eliya, and Ratnapura, watch for landslide warning signs: cracks in ground, tilting trees, sudden changes in water flow. The National Building Research Organisation provides landslide risk maps for Sri Lankan areas.",
                "source": "builtin",
                "chunk_id": 9
            },
            
            # Communication
            {
                "category": "communication",
                "title": "Emergency Communication",
                "content": "Keep battery-powered or hand-crank radio for emergency updates. Text messages often work when voice calls don't. Register with Red Cross Safe and Well website. Have an out-of-state contact as a family communication hub.",
                "source": "builtin",
                "chunk_id": 10
            }
        ]
        
        print(f"Created {len(emergency_documents)} fallback emergency documents")
        return emergency_documents
    
    def build_vector_database(self, documents: List[Dict] = None, force_rebuild: bool = False):
        """
        Build vector database from documents with improved filtering and categorization
        """
        if documents is None:
            # Process PDFs first, fallback to hardcoded if no PDFs
            documents = self.process_all_pdfs(force_rebuild=force_rebuild)
        
        if not documents:
            print("No documents provided for building database!")
            return False
        
        print(f"Starting with {len(documents)} documents")
        
        # Additional filtering and categorization for existing documents
        relevant_documents = []
        categorization_stats = {
            "total_processed": 0,
            "passed_relevance": 0,
            "failed_relevance": 0,
            "category_assigned": 0,
            "category_failed": 0
        }
        
        for doc in documents:
            categorization_stats["total_processed"] += 1
            
            # Check if document already has good relevance score
            if 'relevance_score' in doc and doc['relevance_score'] >= self.content_relevance_threshold:
                categorization_stats["passed_relevance"] += 1
                
                # Check if it has a valid category assignment
                if 'category_confidence' in doc and doc['category_confidence'] >= self.category_similarity_threshold:
                    categorization_stats["category_assigned"] += 1
                    relevant_documents.append(doc)
                    continue
            
            # Re-check relevance for documents without scores or with low scores
            print(f"Re-evaluating document: {doc.get('title', 'Unknown')[:50]}...")
            
            is_relevant, relevance_score = self.is_emergency_relevant_content(doc['content'])
            
            if not is_relevant:
                categorization_stats["failed_relevance"] += 1
                print(f"  ❌ Filtered out - low relevance score: {relevance_score:.3f}")
                continue
            
            categorization_stats["passed_relevance"] += 1
            doc['relevance_score'] = relevance_score
            
            # Determine or re-determine category
            category, category_confidence, category_relevant = self.determine_content_category(doc['content'])
            
            if not category_relevant:
                categorization_stats["category_failed"] += 1
                print(f"  ❌ Filtered out - low category confidence: {category_confidence:.3f}")
                continue
            
            # Update document with new category info
            doc['category'] = category
            doc['category_confidence'] = category_confidence
            categorization_stats["category_assigned"] += 1
            
            print(f"  ✅ Assigned to {self.emergency_categories[category]['name']} (confidence: {category_confidence:.3f})")
            relevant_documents.append(doc)
        
        # Print processing statistics
        print(f"\nDocument Processing Statistics:")
        print(f"  Total documents processed: {categorization_stats['total_processed']}")
        print(f"  Passed relevance check: {categorization_stats['passed_relevance']}")
        print(f"  Failed relevance check: {categorization_stats['failed_relevance']}")
        print(f"  Successfully categorized: {categorization_stats['category_assigned']}")
        print(f"  Failed categorization: {categorization_stats['category_failed']}")
        print(f"  Final document count: {len(relevant_documents)}")
        
        self.documents = relevant_documents
        
        if not relevant_documents:
            print("❌ No relevant documents to process after filtering!")
            print("Consider lowering the relevance threshold or checking your PDF content.")
            return False
        
        # Create embeddings for all documents
        texts = [doc["content"] for doc in relevant_documents]
        print(f"\n🔄 Creating embeddings for {len(texts)} documents...")
        
        try:
            self.embeddings = self.model.encode(texts, show_progress_bar=True)
            
            # Create FAISS index
            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner Product for similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(self.embeddings)
            self.index.add(self.embeddings)
            
            print(f"✅ Vector database built successfully with {self.index.ntotal} documents")
            
            # Print category distribution and quality metrics
            self.print_category_distribution()
            
            return True
            
        except Exception as e:
            print(f"❌ Error building vector database: {str(e)}")
            return False
    
    def add_documents_to_existing_db(self, new_documents: List[Dict]):
        """
        Add new documents to existing database without full rebuild
        """
        if not new_documents:
            print("No new documents to add")
            return False
        
        print(f"Adding {len(new_documents)} new documents to existing database...")
        
        # Filter and categorize new documents
        filtered_documents = []
        
        for doc in new_documents:
            # Check relevance
            is_relevant, relevance_score = self.is_emergency_relevant_content(doc['content'])
            
            if not is_relevant:
                print(f"  ❌ Filtered out irrelevant document: {doc.get('title', 'Unknown')[:50]}")
                continue
            
            # Determine category
            category, category_confidence, category_relevant = self.determine_content_category(doc['content'])
            
            if not category_relevant:
                print(f"  ❌ Filtered out low-confidence document: {doc.get('title', 'Unknown')[:50]}")
                continue
            
            # Update document with scores
            doc['relevance_score'] = relevance_score
            doc['category'] = category
            doc['category_confidence'] = category_confidence
            
            filtered_documents.append(doc)
            print(f"  ✅ Added: {doc.get('title', 'Unknown')[:50]} -> {self.emergency_categories[category]['name']}")
        
        if not filtered_documents:
            print("❌ No documents passed filtering criteria")
            return False
        
        try:
            # Add to documents list
            self.documents.extend(filtered_documents)
            
            # Create embeddings for new documents only
            new_texts = [doc["content"] for doc in filtered_documents]
            new_embeddings = self.model.encode(new_texts, show_progress_bar=True)
            
            # Normalize new embeddings
            faiss.normalize_L2(new_embeddings)
            
            # Add to existing embeddings and index
            if self.embeddings is not None:
                self.embeddings = np.vstack([self.embeddings, new_embeddings])
            else:
                self.embeddings = new_embeddings
            
            # Add to index
            if self.index is None:
                dimension = new_embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dimension)
            
            self.index.add(new_embeddings)
            
            print(f"✅ Successfully added {len(filtered_documents)} new documents to existing database")
            
            # Print updated statistics
            self.print_category_distribution()
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding documents to database: {str(e)}")
            return False




    def search(self, query: str, k: int = 3) -> List[Tuple[Dict, float]]:
        """
        Search for relevant documents
        """
        if self.index is None:
            return []
        
        # Encode query
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.documents):
                results.append((self.documents[idx], float(score)))
        
        return results
    
    def save_locally(self):
        """
        Save vector database to local files
        """
        try:
            # Save documents
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            # Save embeddings
            np.save(self.embeddings_path, self.embeddings)
            
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            
            # Save metadata
            metadata = {
                "model_name": getattr(self.model, 'model_name', "all-MiniLM-L6-v2"),
                "num_documents": len(self.documents),
                "embedding_dimension": self.embeddings.shape[1] if self.embeddings is not None else None,
                "created_at": str(np.datetime64('now')),
                "source_breakdown": self._get_source_breakdown()
            }
            
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Vector database saved to {self.storage_path}")
            return True
            
        except Exception as e:
            print(f"Error saving locally: {str(e)}")
            return False
    
    def _get_source_breakdown(self) -> Dict:
        """
        Get breakdown of documents by source
        """
        breakdown = {}
        for doc in self.documents:
            source = doc.get('source', 'unknown')
            if source in breakdown:
                breakdown[source] += 1
            else:
                breakdown[source] = 1
        return breakdown
    
    def load_locally(self):
        """
        Load vector database from local files
        """
        try:
            # Check if all required files exist
            required_files = [self.documents_path, self.embeddings_path, self.index_path]
            if not all(os.path.exists(f) for f in required_files):
                return False
            
            # Load documents
            with open(self.documents_path, 'rb') as f:
                self.documents = pickle.load(f)
            
            # Load embeddings
            self.embeddings = np.load(self.embeddings_path)
            
            # Load FAISS index
            self.index = faiss.read_index(self.index_path)
            
            print(f"Vector database loaded from {self.storage_path}")
            print(f"Loaded {len(self.documents)} documents")
            return True
            
        except Exception as e:
            print(f"Error loading locally: {str(e)}")
            return False
    
    def get_database_info(self):
        """
        Get information about the current database
        """
        if not os.path.exists(self.metadata_path):
            return None
        
        try:
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def database_exists(self):
        """
        Check if database files exist locally
        """
        required_files = [self.documents_path, self.embeddings_path, self.index_path]
        return all(os.path.exists(f) for f in required_files)
    
    def get_pdf_status(self):
        """
        Get status of PDF files in the directory
        """
        pdf_files = glob.glob(os.path.join(self.pdf_path, "*.pdf"))
        return {
            "pdf_directory": self.pdf_path,
            "pdf_count": len(pdf_files),
            "pdf_files": [os.path.basename(f) for f in pdf_files],
            "directory_exists": os.path.exists(self.pdf_path)
        }
    
    def get_database_stats(self):
        """
        Get comprehensive database statistics
        """
        if not self.documents:
            return {}
        
        stats = {
            "total_documents": len(self.documents),
            "categories": {},
            "sources": {},
            "avg_relevance_score": 0,
            "avg_category_confidence": 0
        }
        
        relevance_scores = []
        category_confidences = []
        
        for doc in self.documents:
            # Category distribution
            category = doc.get('category', 'unknown')
            if category not in stats["categories"]:
                stats["categories"][category] = {
                    "count": 0,
                    "name": self.emergency_categories.get(category, {}).get('name', category)
                }
            stats["categories"][category]["count"] += 1
            
            # Source distribution
            source = doc.get('source', 'unknown')
            stats["sources"][source] = stats["sources"].get(source, 0) + 1
            
            # Quality scores
            if 'relevance_score' in doc:
                relevance_scores.append(doc['relevance_score'])
            if 'category_confidence' in doc:
                category_confidences.append(doc['category_confidence'])
        
        if relevance_scores:
            stats["avg_relevance_score"] = sum(relevance_scores) / len(relevance_scores)
        if category_confidences:
            stats["avg_category_confidence"] = sum(category_confidences) / len(category_confidences)
        
        return stats