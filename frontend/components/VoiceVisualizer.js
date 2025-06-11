// /frontend/components/VoiceVisualizer.js

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import styles from '../styles/VoiceVisualizer.module.css';

export default function VoiceVisualizer() {
  const [bars, setBars] = useState(Array(5).fill(0));

  useEffect(() => {
    const interval = setInterval(() => {
      setBars(prev => prev.map(() => Math.random() * 100));
    }, 100);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className={styles.visualizer}>
      {bars.map((height, index) => (
        <motion.div
          key={index}
          className={styles.bar}
          animate={{ height: `${height}%` }}
          transition={{ duration: 0.1 }}
        />
      ))}
    </div>
  );
}
