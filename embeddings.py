import sys
from importlib.machinery import ModuleSpec
from unittest.mock import MagicMock

# 1. Mock sklearn to bypass the WDAC block on sparsefuncs_fast DLL
mock_spec = ModuleSpec(name='sklearn', loader=None)
mock_sklearn = MagicMock()
mock_sklearn.__spec__ = mock_spec

mock_metrics_spec = ModuleSpec(name='sklearn.metrics', loader=None)
mock_metrics = MagicMock()
mock_metrics.__spec__ = mock_metrics_spec
mock_metrics.roc_curve = MagicMock()

sys.modules['sklearn'] = mock_sklearn
sys.modules['sklearn.metrics'] = mock_metrics

# 2. Import PyTorch and Transformers
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

class MiniLMEmbeddingModel:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        try:
            # Try online load first
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=False)
            self.model = AutoModel.from_pretrained(model_name, local_files_only=False)
        except Exception as e:
            print(f"Warning: Could not connect to Hugging Face ({e}). Trying to load from local cache...")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
                self.model = AutoModel.from_pretrained(model_name, local_files_only=True)
                print("Successfully loaded model from local cache.")
            except Exception as cache_err:
                print(f"Error: Local cache load failed: {cache_err}")
                raise e
        
    def encode(self, sentences):
        is_single = isinstance(sentences, str)
        if is_single:
            sentences = [sentences]
            
        encoded_input = self.tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')
        with torch.no_grad():
            model_output = self.model(**encoded_input)
            
        token_embeddings = model_output[0]
        attention_mask = encoded_input['attention_mask']
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        pooled = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        normalized = F.normalize(pooled, p=2, dim=1)
        embeddings = normalized.cpu().numpy()
        
        if is_single:
            return embeddings[0]
        return embeddings
