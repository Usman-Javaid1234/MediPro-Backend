from supabase import create_client, Client
from app.config import settings
from functools import lru_cache


@lru_cache()
def get_supabase_client() -> Client:
    """
    Create and cache Supabase client instance
    
    Returns:
        Supabase client
    """
    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )
    return supabase


@lru_cache()
def get_supabase_admin_client() -> Client:
    """
    Create and cache Supabase admin client with service role key
    Used for admin operations that bypass RLS
    
    Returns:
        Supabase admin client
    """
    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )
    return supabase


# Global instances
supabase_client = get_supabase_client()
supabase_admin = get_supabase_admin_client()