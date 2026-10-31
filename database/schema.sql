CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    event_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_date DATE NOT NULL,
    location TEXT NOT NULL,
    guest_count INTEGER NOT NULL CHECK (guest_count > 0),
    total_budget NUMERIC(12,2) NOT NULL CHECK (total_budget > 0),
    currency VARCHAR(10) DEFAULT 'INR',
    theme TEXT,
    event_style TEXT,
    event_description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    estimated_amount NUMERIC(12,2) DEFAULT 0,
    actual_amount NUMERIC(12,2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    task_name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    deadline DATE,
    priority TEXT DEFAULT 'Medium',
    status TEXT DEFAULT 'Pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    vendor_name TEXT NOT NULL,
    category TEXT NOT NULL,
    contact_number TEXT,
    email TEXT,
    website TEXT,
    quoted_price NUMERIC(12,2) DEFAULT 0,
    booking_status TEXT DEFAULT 'Not Contacted',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    recommendation_type TEXT NOT NULL,
    content JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_budgets_event_id ON budgets(event_id);
CREATE INDEX idx_tasks_event_id ON tasks(event_id);
CREATE INDEX idx_vendors_event_id ON vendors(event_id);
CREATE INDEX idx_chat_event_id ON chat_history(event_id);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own profiles" ON profiles FOR ALL USING (auth.uid() = id) WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can manage their own events" ON events FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can manage their own budgets" ON budgets FOR ALL USING (
    EXISTS (SELECT 1 FROM events e WHERE e.id = budgets.event_id AND e.user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM events e WHERE e.id = budgets.event_id AND e.user_id = auth.uid())
);
CREATE POLICY "Users can manage their own tasks" ON tasks FOR ALL USING (
    EXISTS (SELECT 1 FROM events e WHERE e.id = tasks.event_id AND e.user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM events e WHERE e.id = tasks.event_id AND e.user_id = auth.uid())
);
CREATE POLICY "Users can manage their own vendors" ON vendors FOR ALL USING (
    EXISTS (SELECT 1 FROM events e WHERE e.id = vendors.event_id AND e.user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM events e WHERE e.id = vendors.event_id AND e.user_id = auth.uid())
);
CREATE POLICY "Users can manage their own chat history" ON chat_history FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can manage their own recommendations" ON recommendations FOR ALL USING (
    EXISTS (SELECT 1 FROM events e WHERE e.id = recommendations.event_id AND e.user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM events e WHERE e.id = recommendations.event_id AND e.user_id = auth.uid())
);
