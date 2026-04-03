-- Seed data for Docker init (seed_db.py is preferred for local dev with proper bcrypt hashes)
-- For Docker: this file runs after schema.sql via /docker-entrypoint-initdb.d/
-- WARNING: The bcrypt hash below may need regeneration. Use seed_db.py for guaranteed working hashes.

INSERT INTO users (username, email, password_hash, role, first_name, last_name) VALUES
('admin', 'admin@academie.fr', '$2b$12$LJ3m4ys3Lk0TSwMCkVc3eOZFkVHBMhCx7Nk8AftHbQz/R5rX.Fkiy', 'admin', 'Marie', 'Dupont'),
('prof.martin', 'martin@academie.fr', '$2b$12$LJ3m4ys3Lk0TSwMCkVc3eOZFkVHBMhCx7Nk8AftHbQz/R5rX.Fkiy', 'professor', 'Jean', 'Martin'),
('prof.bernard', 'bernard@academie.fr', '$2b$12$LJ3m4ys3Lk0TSwMCkVc3eOZFkVHBMhCx7Nk8AftHbQz/R5rX.Fkiy', 'professor', 'Sophie', 'Bernard'),
('etudiant.durand', 'durand@etu.academie.fr', '$2b$12$LJ3m4ys3Lk0TSwMCkVc3eOZFkVHBMhCx7Nk8AftHbQz/R5rX.Fkiy', 'student', 'Lucas', 'Durand'),
('etudiant.petit', 'petit@etu.academie.fr', '$2b$12$LJ3m4ys3Lk0TSwMCkVc3eOZFkVHBMhCx7Nk8AftHbQz/R5rX.Fkiy', 'student', 'Emma', 'Petit'),
('etudiant.moreau', 'moreau@etu.academie.fr', '$2b$12$LJ3m4ys3Lk0TSwMCkVc3eOZFkVHBMhCx7Nk8AftHbQz/R5rX.Fkiy', 'student', 'Hugo', 'Moreau'),
('etudiant.leroy', 'leroy@etu.academie.fr', '$2b$12$LJ3m4ys3Lk0TSwMCkVc3eOZFkVHBMhCx7Nk8AftHbQz/R5rX.Fkiy', 'student', 'Lea', 'Leroy'),
('etudiant.roux', 'roux@etu.academie.fr', '$2b$12$LJ3m4ys3Lk0TSwMCkVc3eOZFkVHBMhCx7Nk8AftHbQz/R5rX.Fkiy', 'student', 'Nathan', 'Roux');

INSERT INTO classes (name, description) VALUES
('GCS2-A', 'Guardia Cybersecurity School - 2eme annee - Groupe A'),
('GCS2-B', 'Guardia Cybersecurity School - 2eme annee - Groupe B');

INSERT INTO class_students (class_id, student_id) VALUES
(1, 4), (1, 5), (1, 6),
(2, 7), (2, 8);

INSERT INTO class_professors (class_id, professor_id) VALUES
(1, 2), (1, 3),
(2, 2);

INSERT INTO subjects (name, class_id, professor_id) VALUES
('DevSecOps', 1, 2),
('Cryptographie', 1, 3),
('Securite Reseaux', 2, 2);

INSERT INTO schedules (class_id, subject_id, day_of_week, start_time, end_time, room) VALUES
(1, 1, 'Lundi', '09:00', '12:00', 'Salle 101'),
(1, 1, 'Mercredi', '14:00', '17:00', 'Salle 101'),
(1, 2, 'Mardi', '09:00', '12:00', 'Salle 203'),
(1, 2, 'Jeudi', '14:00', '16:00', 'Salle 203'),
(2, 3, 'Lundi', '14:00', '17:00', 'Salle 105'),
(2, 3, 'Vendredi', '09:00', '12:00', 'Salle 105');

INSERT INTO evaluations (title, subject_id, professor_id, date, coefficient) VALUES
('Projet Flask Securise', 1, 2, '2026-04-10', 3.0),
('QCM DevSecOps', 1, 2, '2026-03-28', 1.0),
('Examen Cryptographie', 2, 3, '2026-04-05', 2.0),
('TP Securite Reseaux', 3, 2, '2026-04-08', 2.0);

INSERT INTO grades (evaluation_id, student_id, score, comment) VALUES
(2, 4, 15.50, 'Bon travail'),
(2, 5, 17.00, 'Excellent'),
(2, 6, 12.00, 'Peut mieux faire'),
(3, 4, 14.00, 'Satisfaisant'),
(3, 5, 18.50, 'Tres bien'),
(3, 6, 11.00, 'Insuffisant'),
(4, 7, 16.00, 'Bonne maitrise'),
(4, 8, 13.50, 'Correct');
