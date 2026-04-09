import json
import os
from langchain_core.stores import InMemoryStore
from langchain_core.documents import Document

class PersistentInMemoryStore(InMemoryStore):
    """
    A custom resilient file store that wraps InMemoryStore and natively persists to JSON.
    This completely sidesteps the LangChain Storage ecosystem missing LocalFileStore errors!
    """
    def __init__(self, save_path: str):
        super().__init__()
        self.save_path = save_path
        if os.path.exists(save_path):
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.store = {k: Document(**v) for k, v in data.items()}
                
    def mset(self, key_value_pairs: list) -> None:
        super().mset(key_value_pairs)
        self._save()
        
    def mdelete(self, keys: list) -> None:
        super().mdelete(keys)
        self._save()
        
    def _save(self) -> None:
        folder = os.path.dirname(self.save_path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(self.save_path, "w", encoding="utf-8") as f:
            data = {k: {"page_content": v.page_content, "metadata": v.metadata} for k, v in self.store.items()}
            json.dump(data, f, ensure_ascii=False)
