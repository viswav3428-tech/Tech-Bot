-- ============================================================
-- TEACHBOT Database Schema (PostgreSQL / Supabase)
-- Smart India Hackathon (SIH) - Student Innovation Category
-- ============================================================

-- 1. FACULTY
CREATE TABLE IF NOT EXISTS faculty (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    department VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. STUDENTS
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    roll_number VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    department VARCHAR(100),
    semester INT,
    face_encoding_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. ROBOTS
CREATE TABLE IF NOT EXISTS robots (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    model VARCHAR(100) DEFAULT 'TEACHBOT v1.0',
    last_seen_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. LOCATIONS (Named map coordinates for Nav2 / SLAM)
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) UNIQUE NOT NULL,
    map_x DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    map_y DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    floor INT DEFAULT 1,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. ROBOT STATUS LOG
CREATE TABLE IF NOT EXISTS robot_status_log (
    id SERIAL PRIMARY KEY,
    robot_id INT REFERENCES robots(id) ON DELETE CASCADE,
    battery_percent INT,
    mode VARCHAR(50),  -- 'idle', 'following', 'navigating', 'delivering', 'manual'
    pos_x DOUBLE PRECISION,
    pos_y DOUBLE PRECISION,
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. TASKS (Single funnel for all robot commands)
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    robot_id INT REFERENCES robots(id) ON DELETE CASCADE,
    faculty_id INT REFERENCES faculty(id) ON DELETE SET NULL,
    task_type VARCHAR(50) NOT NULL,  -- 'follow', 'goto', 'deliver', 'stop', 'dock'
    destination_id INT REFERENCES locations(id) ON DELETE SET NULL,
    requested_via VARCHAR(50) DEFAULT 'app', -- 'app', 'touchscreen', 'voice_agent', 'dashboard'
    status VARCHAR(50) DEFAULT 'pending',    -- 'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 7. DELIVERIES (Point-to-point delivery tracking)
CREATE TABLE IF NOT EXISTS deliveries (
    id SERIAL PRIMARY KEY,
    task_id INT REFERENCES tasks(id) ON DELETE CASCADE,
    sender_faculty_id INT REFERENCES faculty(id),
    recipient_faculty_id INT REFERENCES faculty(id),
    destination_id INT REFERENCES locations(id),
    item_description TEXT,
    otp_code VARCHAR(10),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_transit', 'delivered', 'failed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. ATTENDANCE SESSIONS & RECORDS (Mandatory faculty review)
CREATE TABLE IF NOT EXISTS attendance_sessions (
    id SERIAL PRIMARY KEY,
    faculty_id INT REFERENCES faculty(id),
    subject_code VARCHAR(50) NOT NULL,
    location_id INT REFERENCES locations(id),
    is_confirmed BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confirmed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS attendance_records (
    id SERIAL PRIMARY KEY,
    session_id INT REFERENCES attendance_sessions(id) ON DELETE CASCADE,
    student_id INT REFERENCES students(id) ON DELETE CASCADE,
    confidence_score DOUBLE PRECISION,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_present BOOLEAN DEFAULT TRUE,
    UNIQUE (session_id, student_id)
);

-- 9. PRESENTATIONS (Slides for Pi 3 HDMI projector)
CREATE TABLE IF NOT EXISTS presentations (
    id SERIAL PRIMARY KEY,
    faculty_id INT REFERENCES faculty(id),
    title VARCHAR(255) NOT NULL,
    file_url TEXT,
    total_slides INT DEFAULT 1,
    current_slide INT DEFAULT 1,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. CHAT SESSIONS & MESSAGES (Conversational AI Assistant)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    robot_id INT REFERENCES robots(id) ON DELETE SET NULL,
    faculty_id INT REFERENCES faculty(id) ON DELETE SET NULL,
    title VARCHAR(255) DEFAULT 'Chat Session',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INT REFERENCES chat_sessions(id) ON DELETE CASCADE,
    sender VARCHAR(50) NOT NULL, -- 'user' | 'assistant'
    message TEXT NOT NULL,
    animation VARCHAR(100),       -- animation tag for Pi 3 touchscreen
    task_id INT REFERENCES tasks(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SEED INITIAL LOCATIONS (Optional sample data)
INSERT INTO locations (name, map_x, map_y, floor, description)
VALUES 
    ('Lab 1', 2.5, 4.0, 1, 'ECE Hardware & Robotics Lab'),
    ('Lab 2', 8.0, 4.0, 1, 'Embedded Systems Lab'),
    ('Faculty Office', 1.0, 10.5, 1, 'Department Faculty Cabins'),
    ('Seminar Hall', 15.0, 6.0, 1, 'Main Auditorium'),
    ('Charging Dock', 0.0, 0.0, 1, 'Base Station & Charging Dock')
ON CONFLICT (name) DO NOTHING;

INSERT INTO robots (id, name, model)
VALUES (1, 'TEACHBOT-01', 'TEACHBOT v1.0')
ON CONFLICT (id) DO NOTHING;
