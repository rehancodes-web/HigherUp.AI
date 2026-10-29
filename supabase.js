import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const SUPABASE_URL = 'https://kgubkabyljxawnsonjnj.supabase.co';
const SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_XlsiXHyiKr6D6LZjByRlsQ_ecy7RNV7';

export const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);