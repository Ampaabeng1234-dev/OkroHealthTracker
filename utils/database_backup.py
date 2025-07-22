"""
Database backup utility for OkroHealthDetector
Exports all database data to JSON format for backup and restore purposes.
"""

import json
import os
from datetime import datetime
from flask import current_app
from database_models import (
    User, Prediction, UserFeedback, SystemLog, DiseaseClass, 
    UserProfile, TrainingData, ModelTraining, ChatbotConfig, 
    ChatConversation, ChatMessage, db
)


class DatabaseBackup:
    def __init__(self):
        self.backup_dir = 'backups'
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Create backup directory if it doesn't exist"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def serialize_model(self, model_instance):
        """Convert SQLAlchemy model instance to dictionary"""
        result = {}
        for column in model_instance.__table__.columns:
            value = getattr(model_instance, column.name)
            
            # Handle datetime objects
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        
        return result
    
    def export_table_data(self, model_class, table_name):
        """Export data from a specific table"""
        try:
            records = model_class.query.all()
            data = []
            
            for record in records:
                data.append(self.serialize_model(record))
            
            return {
                'table_name': table_name,
                'record_count': len(data),
                'data': data
            }
        except Exception as e:
            current_app.logger.error(f"Error exporting {table_name}: {str(e)}")
            return {
                'table_name': table_name,
                'record_count': 0,
                'data': [],
                'error': str(e)
            }
    
    def create_full_backup(self):
        """Create complete database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Define all tables to backup
        tables_to_backup = [
            (User, 'users'),
            (Prediction, 'predictions'),
            (UserFeedback, 'user_feedback'),
            (SystemLog, 'system_logs'),
            (DiseaseClass, 'disease_classes'),
            (UserProfile, 'user_profiles'),
            (TrainingData, 'training_data'),
            (ModelTraining, 'model_training'),
            (ChatbotConfig, 'chatbot_config'),
            (ChatConversation, 'chat_conversations'),
            (ChatMessage, 'chat_messages'),
        ]
        
        backup_data = {
            'backup_info': {
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'application': 'OkroHealthDetector',
                'total_tables': len(tables_to_backup)
            },
            'tables': {}
        }
        
        # Export each table
        total_records = 0
        for model_class, table_name in tables_to_backup:
            table_data = self.export_table_data(model_class, table_name)
            backup_data['tables'][table_name] = table_data
            total_records += table_data['record_count']
        
        backup_data['backup_info']['total_records'] = total_records
        
        # Save to file
        filename = f"okro_backup_{timestamp}.json"
        filepath = os.path.join(self.backup_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            # Get file size
            file_size = os.path.getsize(filepath)
            backup_data['backup_info']['file_size'] = file_size
            backup_data['backup_info']['filename'] = filename
            backup_data['backup_info']['filepath'] = filepath
            
            current_app.logger.info(f"Database backup created: {filename}")
            return backup_data['backup_info']
            
        except Exception as e:
            current_app.logger.error(f"Error creating backup file: {str(e)}")
            raise e
    
    def get_backup_files(self):
        """Get list of available backup files"""
        try:
            backups = []
            if os.path.exists(self.backup_dir):
                for filename in os.listdir(self.backup_dir):
                    if filename.endswith('.json') and 'okro_backup_' in filename:
                        filepath = os.path.join(self.backup_dir, filename)
                        stat = os.stat(filepath)
                        
                        backups.append({
                            'filename': filename,
                            'filepath': filepath,
                            'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'size_mb': round(stat.st_size / (1024 * 1024), 2)
                        })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            current_app.logger.error(f"Error getting backup files: {str(e)}")
            return []
    
    def restore_from_backup(self, backup_filepath):
        """Restore database from backup file (use with caution)"""
        try:
            with open(backup_filepath, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # This is a placeholder for restore functionality
            # Implementation would require careful handling of foreign keys
            # and potentially clearing existing data
            
            current_app.logger.info(f"Backup file loaded: {backup_filepath}")
            return {
                'status': 'loaded',
                'backup_info': backup_data.get('backup_info', {}),
                'tables': list(backup_data.get('tables', {}).keys())
            }
            
        except Exception as e:
            current_app.logger.error(f"Error loading backup file: {str(e)}")
            raise e
    
    def get_database_stats(self):
        """Get current database statistics"""
        try:
            stats = {}
            
            # Count records in each table
            tables = [
                (User, 'users'),
                (Prediction, 'predictions'), 
                (UserFeedback, 'user_feedback'),
                (SystemLog, 'system_logs'),
                (DiseaseClass, 'disease_classes'),
                (UserProfile, 'user_profiles'),
                (TrainingData, 'training_data'),
                (ModelTraining, 'model_training'),
                (ChatbotConfig, 'chatbot_config'),
                (ChatConversation, 'chat_conversations'),
                (ChatMessage, 'chat_messages'),
            ]
            
            total_records = 0
            for model_class, table_name in tables:
                try:
                    count = model_class.query.count()
                    stats[table_name] = count
                    total_records += count
                except Exception as e:
                    stats[table_name] = f"Error: {str(e)}"
            
            stats['total_records'] = total_records
            stats['generated_at'] = datetime.now().isoformat()
            
            return stats
            
        except Exception as e:
            current_app.logger.error(f"Error getting database stats: {str(e)}")
            return {'error': str(e)}