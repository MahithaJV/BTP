import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://uussvxavrtedkmtpnrbg.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_WqPjuyPSfDvvXhxzfy_5XQ_d2Ga5reN';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
