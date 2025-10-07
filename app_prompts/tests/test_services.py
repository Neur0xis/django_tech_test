from django.test import TestCase
from .. import services


class ServiceLayerTests(TestCase):
    """Tests for Phase 3: Service layer functions."""

    def test_generate_response_creates_valid_response(self):
        """Test that generate_response creates a non-empty string."""
        response = services.generate_response('Test prompt')
        
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_get_embedding_returns_384_dimensions(self):
        """Test that get_embedding returns 384-dimensional vector."""
        embedding = services.get_embedding('Test text')
        
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 384)
        self.assertTrue(all(isinstance(x, float) for x in embedding))

    def test_get_embedding_is_deterministic(self):
        """Test that same text produces same embedding."""
        text = 'Consistent text'
        embedding1 = services.get_embedding(text)
        embedding2 = services.get_embedding(text)
        
        self.assertEqual(embedding1, embedding2)

    def test_get_embedding_is_normalized(self):
        """Test that embeddings are normalized vectors."""
        import numpy as np
        embedding = services.get_embedding('Test')
        norm = np.linalg.norm(embedding)
        
        # Should be approximately 1 (unit vector)
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_initialize_index_creates_faiss_index(self):
        """Test that initialize_index creates a FAISS index."""
        services.initialize_index()
        index = services.get_faiss_index()
        
        self.assertIsNotNone(index)
        self.assertEqual(index.d, 384)  # Dimension check

    def test_add_to_index_increases_index_size(self):
        """Test that add_to_index properly adds vectors."""
        services.initialize_index()
        initial_count = services.get_faiss_index().ntotal
        
        embedding = services.get_embedding('Test')
        services.add_to_index(999, embedding)
        
        new_count = services.get_faiss_index().ntotal
        self.assertEqual(new_count, initial_count + 1)

    def test_find_similar_returns_list_of_tuples(self):
        """Test that find_similar returns correct format."""
        services.initialize_index()
        
        # Add some test embeddings
        for i in range(3):
            embedding = services.get_embedding(f'Test {i}')
            services.add_to_index(i, embedding)
        
        # Search
        query_embedding = services.get_embedding('Test 0')
        results = services.find_similar(query_embedding, top_k=2)
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 2)
        
        if results:
            prompt_id, distance = results[0]
            self.assertIsInstance(prompt_id, int)
            self.assertIsInstance(distance, float)

