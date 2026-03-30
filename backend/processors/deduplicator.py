import pickle

import redis
from datasketch import MinHash

from backend.config import settings

NUM_PERM = 128
SIMILARITY_THRESHOLD = 0.85
REDIS_KEY_PREFIX = "minhash:"

_redis = redis.from_url(settings.REDIS_URL)


def compute_minhash(text: str) -> MinHash:
    m = MinHash(num_perm=NUM_PERM)
    for word in text.lower().split():
        m.update(word.encode("utf-8"))
    return m


def is_duplicate(text: str, post_id: int) -> bool:
    candidate = compute_minhash(text)

    for key in _redis.scan_iter(f"{REDIS_KEY_PREFIX}*"):
        stored = pickle.loads(_redis.get(key))
        if candidate.jaccard(stored) >= SIMILARITY_THRESHOLD:
            return True

    # Store this post's signature
    _redis.set(f"{REDIS_KEY_PREFIX}{post_id}", pickle.dumps(candidate))
    return False
