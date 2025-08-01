"""
RedisWrapper: A wrapper class for Redis operations that handles encoding/decoding automatically.

This wrapper class provides several benefits:
1. Automatic encoding/decoding of values to/from bytes when interacting with Redis
2. Consistent error handling for encoding/decoding operations
3. Simplified interface for common Redis operations
4. Centralized place to modify Redis interaction behavior if needed

The wrapper ensures that all data stored in Redis is properly encoded as bytes
and decoded back to strings when retrieved, preventing encoding-related errors
throughout the application. All data conversion methods use UTF-8 encoding for
maximum Unicode compatibility.
"""

import redis
from typing import Any, Dict, Optional

class RedisWrapper:
    """Wrapper for Redis that handles encoding/decoding automatically."""
    
    def __init__(self, *args, **kwargs):
        self._redis = redis.Redis(*args, **kwargs, decode_responses=False)
    
    def _encode(self, value: Any) -> bytes:
        """
        Convert any value to bytes for Redis storage.
        
        Args:
            value: The value to encode (str, int, float, or any other type)
            
        Returns:
            bytes: The encoded value
        """
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode('utf-8')
        if isinstance(value, (int, float)):
            return str(value).encode('utf-8')
        return str(value).encode('utf-8')
    
    def _decode(self, value: Optional[bytes]) -> Optional[str]:
        """
        Preserve None values while converting bytes from Redis back to a string.
        
        Args:
            value: The bytes value from Redis, or None
            
        Returns:
            str or None: The decoded string, or None if input was None
        """
        if value is None:
            return None
        return value.decode('utf-8')
    
    def _decode_dict(self, d: Dict[bytes, bytes]) -> Dict[str, str]:
        """
        Convert a dictionary with bytes keys and values to strings.
        
        Args:
            d: Dictionary with bytes keys and values from Redis
            
        Returns:
            Dict[str, str]: Dictionary with string keys and values
        """
        return {k.decode('utf-8'): v.decode('utf-8') for k, v in d.items()}
    
    def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis and decode it to a string.
        
        Args:
            key: The key to retrieve
            
        Returns:
            str or None: The decoded string value, or None if the key doesn't exist
        """
        return self._decode(self._redis.get(key))
    
    def set(self, key: str, value: Any) -> bool:
        """
        Store a value in Redis after encoding it to bytes.
        
        Args:
            key: The key to store the value under
            value: The value to store (any type that can be converted to a string)
            
        Returns:
            bool: True if the operation was successful
        """
        return self._redis.set(key, self._encode(value))
    
    def hget(self, key: str, field: str) -> Optional[str]:
        """
        Get a field from a Redis hash and decode it to a string.
        
        Args:
            key: The hash key
            field: The field to retrieve
            
        Returns:
            str or None: The decoded field value, or None if the field doesn't exist
        """
        return self._decode(self._redis.hget(key, self._encode(field)))
    
    def hgetall(self, key: str) -> Dict[str, str]:
        """
        Get all fields from a Redis hash and decode them to strings.
        
        Args:
            key: The hash key
            
        Returns:
            Dict[str, str]: Dictionary with decoded string keys and values
        """
        return self._decode_dict(self._redis.hgetall(key))
    
    def hset(self, key: str, mapping: Dict[str, Any]) -> int:
        """
        Store multiple fields in a Redis hash after encoding them to bytes.
        
        Args:
            key: The hash key
            mapping: Dictionary of field-value pairs to store
            
        Returns:
            int: Number of fields that were added
        """
        encoded_mapping = {self._encode(k): self._encode(v) for k, v in mapping.items()}
        return self._redis.hset(key, mapping=encoded_mapping)
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time on a key.
        
        Args:
            key: The key to set expiration for
            seconds: Number of seconds until expiration
            
        Returns:
            bool: True if the operation was successful
        """
        return self._redis.expire(key, seconds)
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key: The key to delete
            
        Returns:
            bool: True if the key was deleted
        """
        return bool(self._redis.delete(key))
