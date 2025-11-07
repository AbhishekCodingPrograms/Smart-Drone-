"""
Smart Farming Drones - AI Model Training Script
===============================================

This script trains a CNN model for crop health detection using TensorFlow/Keras.
The model classifies crops into three categories: Healthy, Diseased, and Pest-affected.

Author: Smart Farming AI Team
Date: 2024
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import cv2
from PIL import Image
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CropHealthModelTrainer:
    """
    CNN Model Trainer for Crop Health Detection
    """
    
    def __init__(self, img_size=(224, 224), batch_size=32, epochs=50):
        self.img_size = img_size
        self.batch_size = batch_size
        self.epochs = epochs
        self.model = None
        self.history = None
        self.class_names = ['Healthy', 'Diseased', 'Pest-affected']
        
    def create_model(self):
        """
        Create CNN model architecture for crop health detection
        """
        logger.info("Creating CNN model architecture...")
        
        # Use MobileNetV2 as base model for transfer learning
        base_model = MobileNetV2(
            input_shape=(*self.img_size, 3),
            include_top=False,
            weights='imagenet'
        )
        
        # Freeze base model layers
        base_model.trainable = False
        
        # Add custom classification head
        model = keras.Sequential([
            base_model,
            layers.GlobalAveragePooling2D(),
            layers.Dropout(0.2),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(len(self.class_names), activation='softmax')
        ])
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        logger.info(f"Model created with {model.count_params()} parameters")
        return model
    
    def generate_synthetic_data(self, num_samples=1000):
        """
        Generate synthetic crop health data for training
        Since we don't have access to PlantVillage dataset, we'll create synthetic data
        """
        logger.info("Generating synthetic crop health data...")
        
        # Create synthetic images with different characteristics
        images = []
        labels = []
        
        for i in range(num_samples):
            # Generate random image
            img = np.random.randint(0, 255, (*self.img_size, 3), dtype=np.uint8)
            
            # Add different patterns based on health status
            label_idx = i % len(self.class_names)
            
            if label_idx == 0:  # Healthy - green dominant
                img[:, :, 1] = np.clip(img[:, :, 1] + 50, 0, 255)
            elif label_idx == 1:  # Diseased - brown/yellow spots
                # Add brown spots
                spots = np.random.randint(0, 50, (10, 10, 3))
                spots[:, :, 0] = 139  # Brown
                spots[:, :, 1] = 69
                spots[:, :, 2] = 19
                x, y = np.random.randint(0, self.img_size[0]-10), np.random.randint(0, self.img_size[1]-10)
                img[x:x+10, y:y+10] = spots
            else:  # Pest-affected - irregular patterns
                # Add irregular patterns
                noise = np.random.randint(-30, 30, (*self.img_size, 3))
                img = np.clip(img + noise, 0, 255)
            
            images.append(img)
            labels.append(label_idx)
        
        return np.array(images), np.array(labels)
    
    def prepare_data(self):
        """
        Prepare training and validation data
        """
        logger.info("Preparing training data...")
        
        # Generate synthetic data
        X, y = self.generate_synthetic_data(1200)
        
        # Convert labels to categorical
        y_categorical = keras.utils.to_categorical(y, len(self.class_names))
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y_categorical, test_size=0.2, random_state=42, stratify=y
        )
        
        # Data augmentation
        train_datagen = ImageDataGenerator(
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            horizontal_flip=True,
            zoom_range=0.2,
            brightness_range=[0.8, 1.2]
        )
        
        val_datagen = ImageDataGenerator()
        
        train_generator = train_datagen.flow(X_train, y_train, batch_size=self.batch_size)
        val_generator = val_datagen.flow(X_val, y_val, batch_size=self.batch_size)
        
        return train_generator, val_generator, X_val, y_val
    
    def train_model(self):
        """
        Train the CNN model
        """
        logger.info("Starting model training...")
        
        # Create model
        self.create_model()
        
        # Prepare data
        train_gen, val_gen, X_val, y_val = self.prepare_data()
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7
            ),
            keras.callbacks.ModelCheckpoint(
                'model/crop_health_model.h5',
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            )
        ]
        
        # Train model
        self.history = self.model.fit(
            train_gen,
            epochs=self.epochs,
            validation_data=val_gen,
            callbacks=callbacks,
            verbose=1
        )
        
        logger.info("Model training completed!")
        return self.history
    
    def evaluate_model(self, X_val, y_val):
        """
        Evaluate model performance
        """
        logger.info("Evaluating model performance...")
        
        # Predictions
        predictions = self.model.predict(X_val)
        y_pred = np.argmax(predictions, axis=1)
        y_true = np.argmax(y_val, axis=1)
        
        # Classification report
        report = classification_report(y_true, y_pred, target_names=self.class_names)
        logger.info(f"Classification Report:\n{report}")
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        logger.info(f"Confusion Matrix:\n{cm}")
        
        return report, cm
    
    def plot_training_history(self):
        """
        Plot training history
        """
        if self.history is None:
            logger.warning("No training history available")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Plot accuracy
        ax1.plot(self.history.history['accuracy'], label='Training Accuracy')
        ax1.plot(self.history.history['val_accuracy'], label='Validation Accuracy')
        ax1.set_title('Model Accuracy')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Accuracy')
        ax1.legend()
        
        # Plot loss
        ax2.plot(self.history.history['loss'], label='Training Loss')
        ax2.plot(self.history.history['val_loss'], label='Validation Loss')
        ax2.set_title('Model Loss')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Loss')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('model/training_history.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def save_model_info(self):
        """
        Save model information and metadata
        """
        model_info = {
            'model_name': 'Crop Health Detection CNN',
            'version': '1.0',
            'input_shape': (*self.img_size, 3),
            'num_classes': len(self.class_names),
            'class_names': self.class_names,
            'architecture': 'MobileNetV2 + Custom Head',
            'training_samples': 1200,
            'validation_split': 0.2,
            'batch_size': self.batch_size,
            'epochs': self.epochs
        }
        
        with open('model/model_info.json', 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info("Model information saved to model/model_info.json")

def main():
    """
    Main training function
    """
    logger.info("Starting Smart Farming Drones - Crop Health Model Training")
    
    # Create model directory if it doesn't exist
    os.makedirs('model', exist_ok=True)
    
    # Initialize trainer
    trainer = CropHealthModelTrainer(epochs=30)  # Reduced epochs for demo
    
    try:
        # Train model
        history = trainer.train_model()
        
        # Prepare validation data for evaluation
        _, _, X_val, y_val = trainer.prepare_data()
        
        # Evaluate model
        report, cm = trainer.evaluate_model(X_val, y_val)
        
        # Plot training history
        trainer.plot_training_history()
        
        # Save model information
        trainer.save_model_info()
        
        logger.info("Training completed successfully!")
        logger.info(f"Model saved to: model/crop_health_model.h5")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
