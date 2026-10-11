-- ============================================================
-- FeedbackSense AI Database Schema Initialization Script
-- Target RDBMS: MySQL 8.0+
-- Database: feedbacksense_db
-- ============================================================

CREATE DATABASE IF NOT EXISTS `feedbacksense_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `feedbacksense_db`;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` VARCHAR(50) NOT NULL DEFAULT 'user',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Feedback Table
CREATE TABLE IF NOT EXISTS `feedback` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `feedback_text` TEXT NOT NULL,
    `source` VARCHAR(100) NOT NULL DEFAULT 'Manual',
    `product_or_service` VARCHAR(150) NOT NULL DEFAULT 'General',
    `category` VARCHAR(100) NOT NULL DEFAULT 'User Experience',
    `rating` INT NULL,
    `submitted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_feedback_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    INDEX `idx_feedback_category` (`category`),
    INDEX `idx_feedback_source` (`source`),
    INDEX `idx_feedback_submitted_at` (`submitted_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Sentiment Analysis Table
CREATE TABLE IF NOT EXISTS `sentiment_analysis` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `feedback_id` INT NOT NULL UNIQUE,
    `sentiment` VARCHAR(20) NOT NULL, -- Positive, Negative, Neutral
    `confidence_score` FLOAT NOT NULL DEFAULT 0.0,
    `keywords` TEXT NULL,
    `detected_topic` VARCHAR(150) NULL,
    `explanation` TEXT NULL,
    `model_version` VARCHAR(50) NOT NULL DEFAULT 'v1.0.0-tfidf-hybrid',
    `analyzed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_sentiment_feedback` FOREIGN KEY (`feedback_id`) REFERENCES `feedback` (`id`) ON DELETE CASCADE,
    INDEX `idx_sentiment_label` (`sentiment`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Improvement Issues Table
CREATE TABLE IF NOT EXISTS `improvement_issues` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(200) NOT NULL,
    `category` VARCHAR(100) NOT NULL,
    `description` TEXT NULL,
    `occurrence_count` INT NOT NULL DEFAULT 1,
    `priority` VARCHAR(20) NOT NULL DEFAULT 'Medium', -- High, Medium, Low
    `suggested_action` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_issues_category` (`category`),
    INDEX `idx_issues_priority` (`priority`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Issue Feedback Mapping Table (Many-to-Many)
CREATE TABLE IF NOT EXISTS `issue_feedback` (
    `issue_id` INT NOT NULL,
    `feedback_id` INT NOT NULL,
    PRIMARY KEY (`issue_id`, `feedback_id`),
    CONSTRAINT `fk_if_issue` FOREIGN KEY (`issue_id`) REFERENCES `improvement_issues` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_if_feedback` FOREIGN KEY (`feedback_id`) REFERENCES `feedback` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Default Admin User (Password: admin123, hashed using pbkdf2/bcrypt)
INSERT IGNORE INTO `users` (`id`, `name`, `email`, `password_hash`, `role`, `created_at`) 
VALUES (1, 'Admin User', 'admin@feedbacksense.ai', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeg6Lruj3vjPGga31lW', 'admin', NOW());
