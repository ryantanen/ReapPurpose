-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables (in correct order due to foreign key constraints)
DROP TABLE IF EXISTS known_products CASCADE;
DROP TABLE IF EXISTS statistics CASCADE;
DROP TABLE IF EXISTS pantry_items CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;

-- Create user table
CREATE TABLE IF NOT EXISTS "user" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company VARCHAR NOT NULL,
    email VARCHAR,
    hashed_password VARCHAR NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE
);

-- Create pantry_items table
CREATE TABLE IF NOT EXISTS pantry_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    barcode VARCHAR,
    name VARCHAR NOT NULL,
    expires_at VARCHAR NOT NULL,
    lastest_scan_time VARCHAR NOT NULL,
    quantity INTEGER NOT NULL,
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE
);

-- Create statistics table
CREATE TABLE IF NOT EXISTS statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    tracked_items INTEGER NOT NULL DEFAULT 0,
    items_used INTEGER NOT NULL DEFAULT 0,
    total_items INTEGER NOT NULL DEFAULT 0,
    enviroment_impact_co2 FLOAT NOT NULL DEFAULT 0.0,
    enviroment_impact_water FLOAT NOT NULL DEFAULT 0.0
);

-- Create known_products table
CREATE TABLE IF NOT EXISTS known_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    barcode VARCHAR UNIQUE,
    name VARCHAR NOT NULL,
    brand VARCHAR,
    category VARCHAR,
    created_by UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_at VARCHAR NOT NULL,
    updated_at VARCHAR NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_pantry_items_user_id ON pantry_items(user_id);
CREATE INDEX IF NOT EXISTS idx_statistics_user_id ON statistics(user_id);
CREATE INDEX IF NOT EXISTS idx_known_products_created_by ON known_products(created_by);
CREATE INDEX IF NOT EXISTS idx_known_products_barcode ON known_products(barcode);

-- Add comments to tables
COMMENT ON TABLE "user" IS 'Stores user information and authentication details';
COMMENT ON TABLE pantry_items IS 'Stores items in user''s pantry';
COMMENT ON TABLE statistics IS 'Stores user statistics and environmental impact';
COMMENT ON TABLE known_products IS 'Stores known product information'; 