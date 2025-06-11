// /frontend/components/ImageUploadZone.js

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import styles from '../styles/ImageUpload.module.css';

export default function ImageUploadZone({ onUpload, onClose }) {
  const onDrop = useCallback((acceptedFiles) => {
    const imageFiles = acceptedFiles.filter(file => 
      file.type.startsWith('image/')
    );
    onUpload(imageFiles);
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    },
    multiple: true,
    maxFiles: 5
  });

  const overlayVariants = {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 }
  };

  const modalVariants = {
    initial: { opacity: 0, scale: 0.8, y: 50 },
    animate: { 
      opacity: 1, 
      scale: 1, 
      y: 0,
      transition: { type: "spring", stiffness: 260, damping: 20 }
    },
    exit: { opacity: 0, scale: 0.8, y: 50 }
  };

  return (
    <motion.div 
      className={styles.overlay}
      variants={overlayVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      onClick={onClose}
    >
      <motion.div 
        className={styles.modal}
        variants={modalVariants}
        onClick={e => e.stopPropagation()}
      >
        <div className={styles.header}>
          <h3>Upload Images</h3>
          <button onClick={onClose}>×</button>
        </div>
        
        <motion.div 
          {...getRootProps()} 
          className={`${styles.dropzone} ${isDragActive ? styles.active : ''}`}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <input {...getInputProps()} />
          <motion.div 
            className={styles.dropContent}
            animate={isDragActive ? { scale: 1.1 } : { scale: 1 }}
          >
            <div className={styles.icon}>📁</div>
            {isDragActive ? (
              <p>Drop the images here...</p>
            ) : (
              <div>
                <p>Drag & drop images here, or click to select</p>
                <small>Supports PNG, JPG, JPEG, GIF, WebP (max 5 files)</small>
              </div>
            )}
          </motion.div>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}
