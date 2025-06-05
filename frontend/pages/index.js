// /mnt/c/Users/asadi/Desktop/ChatBot/ChatBot_Reop/IndustrialProject/frontend/pages/index.js


import { useState } from 'react';
import ChatWidget from '../components/ChatWidget';
import styles from '../styles/Chat.module.css';

export default function Home() {
  return (
    <div className={styles.container}>
      <main className={styles.main}>
        <h1 className={styles.title}>
          Welcome to <span className={styles.highlight}>AI Assistant</span>
        </h1>
        <p className={styles.description}>
          Experience the future of conversational AI with our advanced chatbot interface.
          Click the chat button in the bottom right to get started!
        </p>
        
        <div className={styles.features}>
          <div className={styles.feature}>
            <h3>🤖 Intelligent Responses</h3>
            <p>Get accurate, context-aware answers to your questions</p>
          </div>
          <div className={styles.feature}>
            <h3>🎨 Dark Mode Support</h3>
            <p>Switch between light and dark themes for comfortable viewing</p>
          </div>
          <div className={styles.feature}>
            <h3>📱 Responsive Design</h3>
            <p>Works seamlessly across all devices and screen sizes</p>
          </div>
          <div className={styles.feature}>
            <h3>🔊 Voice Features</h3>
            <p>Hear responses with text-to-speech technology</p>
          </div>
        </div>
      </main>
      
      <ChatWidget />
    </div>
  );
}
