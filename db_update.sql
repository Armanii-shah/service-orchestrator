-- Add preferred_city to profiles table
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS preferred_city TEXT;

-- (Optional) If you migrate your MOCK_PROVIDERS_DB to Supabase eventually, 
-- you will need the city column on the providers table too:
-- ALTER TABLE public.providers ADD COLUMN IF NOT EXISTS city TEXT;
