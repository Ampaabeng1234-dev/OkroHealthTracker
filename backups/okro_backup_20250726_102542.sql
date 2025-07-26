-- OkroHealthDetector Database Backup
-- Created: 2025-07-26T10:25:42.595800
-- Application: OkroHealthDetector v1.0
-- 

SET foreign_key_checks = 0;

-- 
-- Table: users (4 records)
-- 

DELETE FROM users;

INSERT INTO users (id, username, email, password_hash, role, active, created_at, last_login) VALUES
  (1, 'admin', 'admin@okrohealth.com', 'scrypt:32768:8:1$m67aMQ8fvqgG54Yl$267870a6d8967414d9a9e67ee1d263db081ac99137997ed0dc88796aef4622faa4d9a71cbf820767a7249b9c5f05aa0807689abf7f08f3d20b72190a5210fd1d', 'admin', 0, '2025-07-18T06:56:29.941900', '2025-07-18T07:31:46.622350'),
  (4, 'Ashie', 'izoora4@gmail.com', 'scrypt:32768:8:1$H8e2UnCzyWyYCdDE$8f9e2052371e5962362acac3e84c9c1cb393bc40c57c6e06eed8189d6bde743cd387878087798f4edf3743dc387ded102d91df067a8c3de4f1207225fba5fb85', 'user', 1, '2025-07-18T07:42:32.814919', '2025-07-18T07:58:37.223993'),
  (3, 'Samuel', 'projecthosting425@gmail.com', 'scrypt:32768:8:1$MUe6NANa3ZIRDEhE$d6afc6f952c785995749055d5027961355c439b336a0855005e2092a3aed548fbe47432e963f91f28dde8473c940bc2c209de768dc026286535558f2672ac91e', 'admin', 1, '2025-07-18T07:06:02.973192', '2025-07-22T15:27:08.981383'),
  (2, 'demo_user', 'user@okrohealth.com', 'scrypt:32768:8:1$NEfmzpyrMmBfnJmR$1485e321e8c222b06ee28b9839c4e67f7c6bfedd57f43ed6a5d062426f6d55b6a9bdebae97f7121b1d328a9af237490b4cd560898043b1ae0172c31aa0215b12', 'user', 1, '2025-07-18T06:56:29.941903', '2025-07-22T15:48:43.243072');

-- 
-- Table: predictions (12 records)
-- 

DELETE FROM predictions;

INSERT INTO predictions (id, user_id, filename, original_filename, prediction, confidence, method, created_at, all_probabilities, dl_confidence, rule_confidence, processing_time) VALUES
  (3, 4, 'd8d177db-c9d0-4459-a20d-2d5ffce975db_image00012.jpeg', 'image00012.jpeg', 'Invalid Input', 0.0, 'validation_rejected', '2025-07-18T07:43:17.794995', NULL, NULL, NULL, 7.152557373046875e-07),
  (4, 4, 'b0b0e035-09ae-4145-8a63-461f06ecea53_image00012.jpeg', 'image00012.jpeg', 'Invalid Input', 0.0, 'validation_rejected', '2025-07-18T07:46:48.697082', NULL, NULL, NULL, 7.152557373046875e-07),
  (5, 4, '5d04d203-d9fb-43b4-b468-ce160840d2b8_image00013.jpeg', 'image00013.jpeg', 'Invalid Input', 0.0, 'validation_rejected', '2025-07-18T07:50:07.456103', NULL, NULL, NULL, 7.152557373046875e-07),
  (6, 4, '39be4196-4092-4ee9-924d-f140a4a1357d_image00012.jpeg', 'image00012.jpeg', 'Processing Error', 0.0, 'preprocessing_failed', '2025-07-18T07:58:59.509118', NULL, NULL, NULL, 2.384185791015625e-07),
  (7, 4, '9694c765-7011-43b2-99f1-151f08fb8d56_image00017.jpeg', 'image00017.jpeg', 'Mosaic Virus', 0.6400000000000001, 'hybrid', '2025-07-18T08:03:34.842969', '{"Healthy": 0.20000246167182922, "Bacterial Blight": 0.20002497732639313, "Leaf Spot": 0.2000291645526886, "Mosaic Virus": 0.19978678226470947, "Powdery Mildew": 0.20015664398670197}', 0.20015664398670197, 0.8, 2.384185791015625e-07),
  (8, 4, 'fa368c08-db6c-4442-bbd3-387aea1d19d3_image00012.jpeg', 'image00012.jpeg', 'Leaf Spot', 0.6400000000000001, 'hybrid', '2025-07-18T08:08:33.955297', '{"Healthy": 0.20738965272903442, "Bacterial Blight": 0.19974206387996674, "Leaf Spot": 0.1951475590467453, "Mosaic Virus": 0.19575387239456177, "Powdery Mildew": 0.20196682214736938}', 0.20738965272903442, 0.8, 4.76837158203125e-07),
  (9, 3, '071bdb15-4f83-4763-a062-674c03ebbb8e_image00014.jpeg', 'image00014.jpeg', 'Mosaic Virus', 0.6400000000000001, 'hybrid', '2025-07-21T11:03:09.914787', '{"Healthy": 0.20797502994537354, "Bacterial Blight": 0.19399535655975342, "Leaf Spot": 0.20482617616653442, "Mosaic Virus": 0.19491374492645264, "Powdery Mildew": 0.1982896476984024}', 0.20797502994537354, 0.8, 2.384185791015625e-07),
  (10, 2, '5fb4c3b5-af92-4db3-80ae-bc3267bf4b80_image00016.jpeg', 'image00016.jpeg', 'Mosaic Virus', 0.6400000000000001, 'hybrid', '2025-07-21T11:05:35.915694', '{"Healthy": 0.20506185293197632, "Bacterial Blight": 0.19307298958301544, "Leaf Spot": 0.1998010277748108, "Mosaic Virus": 0.20281481742858887, "Powdery Mildew": 0.19924937188625336}', 0.20506185293197632, 0.8, 4.76837158203125e-07),
  (11, 2, '19c8e136-8499-42d0-b4c4-24d0d8c6501b_R.jpeg', 'R.jpeg', 'Mosaic Virus', 0.6400000000000001, 'hybrid', '2025-07-21T11:06:44.403823', '{"Healthy": 0.2044771909713745, "Bacterial Blight": 0.1927403211593628, "Leaf Spot": 0.20013953745365143, "Mosaic Virus": 0.20141644775867462, "Powdery Mildew": 0.20122645795345306}', 0.2044771909713745, 0.8, 2.384185791015625e-07),
  (12, 2, '9d49d000-9972-4cba-b874-88fe318f6097_okra_bacterial_leaf_spot.jpg', 'okra_bacterial_leaf_spot.jpg', 'Mosaic Virus', 0.6025748062133789, 'hybrid', '2025-07-21T11:07:09.599315', '{"Healthy": 0.2040330320596695, "Bacterial Blight": 0.1916341632604599, "Leaf Spot": 0.20090891420841217, "Mosaic Virus": 0.20429134368896484, "Powdery Mildew": 0.1991325318813324}', 0.20429134368896484, 0.8, 2.384185791015625e-07),
  (13, 2, '1ca11355-0db7-421e-a693-0acedc0eb5d8_IMG-20250115-WA0054.jpg', 'IMG-20250115-WA0054.jpg', 'Leaf Spot', 0.6400000000000001, 'hybrid', '2025-07-22T14:36:35.534301', '{"Healthy": 0.20678600668907166, "Bacterial Blight": 0.1978759765625, "Leaf Spot": 0.2010265588760376, "Mosaic Virus": 0.19938874244689941, "Powdery Mildew": 0.19492267072200775}', 0.20678600668907166, 0.8, 2.384185791015625e-07),
  (14, 2, '7819efbf-1576-4412-881b-9113be423715_image00009.jpeg', 'image00009.jpeg', 'Mosaic Virus', 0.6400000000000001, 'hybrid', '2025-07-22T14:40:26.834849', '{"Healthy": 0.2068922519683838, "Bacterial Blight": 0.19770070910453796, "Leaf Spot": 0.2010364830493927, "Mosaic Virus": 0.19903768599033356, "Powdery Mildew": 0.19533281028270721}', 0.2068922519683838, 0.8, 2.384185791015625e-07);

-- Table user_feedback is empty

-- 
-- Table: system_logs (22 records)
-- 

DELETE FROM system_logs;

INSERT INTO system_logs (id, user_id, event_type, event_data, ip_address, user_agent, created_at) VALUES
  (1, NULL, 'failed_login', '{"username": "user"}', '154.161.25.189, 10.83.2.149', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:11:34.625779'),
  (2, NULL, 'failed_login', '{"username": "user"}', '154.161.25.189, 10.83.3.241', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:12:06.301189'),
  (3, NULL, 'failed_login', '{"username": "user"}', '154.161.25.189, 10.83.2.149', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:12:20.870703'),
  (4, NULL, 'failed_login', '{"username": "user"}', '154.161.25.189, 10.83.3.241', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:12:34.540168'),
  (5, 2, 'login', '{"username": "demo_user"}', '154.161.25.189, 10.83.3.241', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:14:42.234146'),
  (6, 2, 'login', '{"username": "demo_user"}', '154.161.25.189, 10.83.1.74', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:23:24.108261'),
  (7, 1, 'login', '{"username": "admin"}', '154.161.25.189, 10.83.1.74', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:31:46.739977'),
  (8, 3, 'login', '{"username": "Samuel"}', '154.161.25.189, 10.83.3.241', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:37:05.929828'),
  (9, 3, 'user_status_changed', '{"target_user": "admin", "new_status": "deactivated"}', '154.161.25.189, 10.83.1.74', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:38:26.345607'),
  (10, 3, 'logs_cleared', '{"log_type": "predictions"}', '154.161.25.189, 10.83.1.74', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:41:09.909656'),
  (11, 4, 'registration', '{"username": "Ashie", "email": "izoora4@gmail.com", "role": "user"}', '154.161.25.189, 10.83.9.133', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:42:32.925686'),
  (12, 4, 'login', '{"username": "Ashie"}', '154.161.25.189, 10.83.9.133', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T07:58:37.342260'),
  (13, 3, 'login', '{"username": "Samuel"}', '154.161.25.189, 10.83.1.74', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-18T08:11:17.296403'),
  (14, 3, 'login', '{"username": "Samuel"}', '154.161.26.60, 10.83.7.207', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-21T11:01:35.562163'),
  (15, NULL, 'failed_login', '{"username": "Ashie"}', '154.161.26.60, 10.83.1.88', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-21T11:04:54.685946'),
  (16, 2, 'login', '{"username": "demo_user"}', '154.161.26.60, 10.83.5.150', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-21T11:05:01.578643'),
  (17, 2, 'login', '{"username": "demo_user"}', '154.160.6.98, 10.83.6.26', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-22T14:35:29.227379'),
  (18, 3, 'login', '{"username": "Samuel"}', '154.160.6.98, 10.83.1.88', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-22T14:40:50.747324'),
  (19, 3, 'login', '{"username": "Samuel"}', '154.160.6.98, 10.83.3.15', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-22T15:19:50.610281'),
  (20, NULL, 'failed_login', '{"username": "admin"}', '127.0.0.1', 'curl/8.14.1', '2025-07-22T15:22:48.981776'),
  (21, 3, 'login', '{"username": "Samuel"}', '154.160.6.98, 10.83.1.88', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-22T15:27:09.092923'),
  (22, 2, 'login', '{"username": "demo_user"}', '154.160.6.98, 10.83.5.150', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0', '2025-07-22T15:48:43.359238');

-- 
-- Table: disease_classes (5 records)
-- 

DELETE FROM disease_classes;

INSERT INTO disease_classes (id, name, description, treatment, severity_level, active, created_at, updated_at) VALUES
  (1, 'Healthy', 'Plant appears healthy with no visible signs of disease', 'Continue regular care. Monitor plant health regularly.', 1, 1, '2025-07-18T06:56:29.634353', '2025-07-18T06:56:29.634356'),
  (2, 'Bacterial Blight', 'Bacterial infection causing leaf spots and wilting', 'Remove infected leaves. Apply copper-based bactericide. Ensure good drainage.', 4, 1, '2025-07-18T06:56:29.634357', '2025-07-18T06:56:29.634358'),
  (3, 'Leaf Spot', 'Fungal infection causing circular spots on leaves', 'Remove affected leaves. Apply fungicide. Avoid overhead watering.', 3, 1, '2025-07-18T06:56:29.634360', '2025-07-18T06:56:29.634360'),
  (4, 'Mosaic Virus', 'Viral infection causing mottled yellow and green patterns', 'Remove infected plants. Control aphid vectors. Use resistant varieties.', 5, 1, '2025-07-18T06:56:29.634361', '2025-07-18T06:56:29.634362'),
  (5, 'Powdery Mildew', 'Fungal infection causing white powdery coating on leaves', 'Apply sulfur-based fungicide. Improve air circulation. Reduce humidity.', 3, 1, '2025-07-18T06:56:29.634362', '2025-07-18T06:56:29.634362');

-- Table user_profiles is empty

-- 
-- Table: training_data (6 records)
-- 

DELETE FROM training_data;

INSERT INTO training_data (id, filename, original_filename, disease_class, file_path, file_size, image_width, image_height, uploaded_by, upload_date, is_validated, validation_notes) VALUES
  (1, 'demo_healthy_leaf.jpg', 'healthy_leaf.jpg', 'Healthy', 'static/training_data/Healthy/demo_healthy_leaf.jpg', 12345, 224, 224, 1, '2025-07-22T15:23:09.656416', 1, NULL),
  (2, 'demo_healthy_leaf.jpg', 'healthy_leaf.jpg', 'Healthy', 'static/training_data/Healthy/demo_healthy_leaf.jpg', 12345, 224, 224, 1, '2025-07-22T15:23:15.165966', 1, NULL),
  (3, 'demo_bacterial_leaf.jpg', 'bacterial_leaf.jpg', 'Bacterial_Blight', 'static/training_data/Bacterial_Blight/demo_bacterial_leaf.jpg', 15234, 224, 224, 1, '2025-07-22T15:23:23.517344', 1, NULL),
  (4, 'demo_leaf_spot.jpg', 'leaf_spot.jpg', 'Leaf_Spot', 'static/training_data/Leaf_Spot/demo_leaf_spot.jpg', 13456, 224, 224, 1, '2025-07-22T15:23:23.517344', 1, NULL),
  (5, 'demo_mosaic.jpg', 'mosaic_virus.jpg', 'Mosaic_Virus', 'static/training_data/Mosaic_Virus/demo_mosaic.jpg', 14567, 224, 224, 1, '2025-07-22T15:23:23.517344', 1, NULL),
  (6, 'demo_powdery.jpg', 'powdery_mildew.jpg', 'Powdery_Mildew', 'static/training_data/Powdery_Mildew/demo_powdery.jpg', 16789, 224, 224, 1, '2025-07-22T15:23:23.517344', 1, NULL);

-- 
-- Table: model_training (2 records)
-- 

DELETE FROM model_training;

INSERT INTO model_training (id, training_name, model_version, training_status, training_start, training_end, total_images, training_accuracy, validation_accuracy, epochs_completed, total_epochs, model_file_path, training_log, created_by, created_at) VALUES
  (1, 'Demo Training Session', 'demo_v1', 'completed', '2025-07-22T15:23:09.571877', '2025-07-22T15:23:09.571880', 25, 0.92, 0.88, 10, 10, NULL, NULL, 1, '2025-07-22T15:23:09.594416'),
  (2, 'Demo UNet Training', 'demo_v1.0', 'completed', '2025-07-22T13:23:30.492670', '2025-07-22T14:53:30.492670', 25, 0.92, 0.88, 10, 10, NULL, NULL, 1, '2025-07-22T15:23:30.492670');

-- Table chatbot_config is empty

-- Table chat_conversations is empty

-- Table chat_messages is empty

SET foreign_key_checks = 1;

-- Backup completed: 51 total records
