// /frontend/components/ChatMessage.js

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import styles from '../styles/ChatWidget.module.css';

/**
 * Helper: Render message content safely as string.
 * Handles string, object with .content, or array of such objects.
 */
function getTextContent(text) {
  if (typeof text === 'string') return text;
  if (Array.isArray(text)) {
    // If it's an array of message objects, join their content
    return text.map(getTextContent).join(' ');
  }
  if (typeof text === 'object' && text !== null) {
    // If it's a message object with .content
    if ('content' in text) return String(text.content);
    return JSON.stringify(text); // fallback
  }
  return '';
}

export default function ChatMessage({ sender, text, images, timestamp, avatar, sources, animate, index }) {
  const isUser = sender === 'user';
  const [showReactions, setShowReactions] = useState(false);
  const [selectedReaction, setSelectedReaction] = useState(null);
  
  const bubbleClass = isUser ? styles.userBubble : styles.botBubble;
  const containerClass = isUser ? styles.userMsg : styles.botMsg;
  const fadeClass = animate ? styles.fadeIn : '';
  const avatarClass = isUser ? styles.userAvatar : styles.botAvatar;
  const tailClass = isUser ? styles.bubbleTailUser : styles.bubbleTailBot;

  const reactions = ['👍', '👎', '❤️', '😊', '😮', '🤔'];

  const messageVariants = {
    initial: { 
      opacity: 0, 
      x: isUser ? 50 : -50,
      scale: 0.8
    },
    animate: { 
      opacity: 1, 
      x: 0,
      scale: 1,
      transition: {
        delay: index * 0.1,
        type: "spring",
        stiffness: 260,
        damping: 20
      }
    }
  };

  const bubbleVariants = {
    hover: { 
      scale: 1.02,
      transition: { type: "spring", stiffness: 400, damping: 10 }
    }
  };

  // Improved renderText to handle only string input
  const renderText = (rawText) => {
    const safeText = getTextContent(rawText);

    // Code block regex for ``````
    const codeBlockRegex = /``````/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(safeText)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        parts.push(
          <span key={lastIndex}>{safeText.slice(lastIndex, match.index)}</span>
        );
      }

      // Add code block
      const language = match[1] || 'javascript';
      const code = match[2].trim();
      parts.push(
        <motion.div 
          key={match.index}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <SyntaxHighlighter
            language={language}
            style={tomorrow}
            customStyle={{
              margin: '10px 0',
              borderRadius: '8px',
              fontSize: '14px'
            }}
          >
            {code}
          </SyntaxHighlighter>
        </motion.div>
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < safeText.length) {
      parts.push(
        <span key={lastIndex}>{safeText.slice(lastIndex)}</span>
      );
    }

    return parts.length > 0 ? parts : safeText;
  };

  const handleReaction = (reaction) => {
    setSelectedReaction(reaction);
    setShowReactions(false);
    // Here you could send the reaction to your backend
  };

  return (
    <motion.div 
      className={`${containerClass} ${fadeClass}`}
      variants={messageVariants}
      initial="initial"
      animate="animate"
    >
      <motion.div 
        className={avatarClass}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        <img
          src={avatar}
          alt={`${sender} avatar`}
          width="32"
          height="32"
          style={{ borderRadius: '50%', objectFit: 'cover', background: '#fff' }}
          onError={e => { 
            e.target.onerror = null; 
            e.target.src = sender === 'user' ? '/user-avatar.png' : '/bot-avatar.png'; 
          }}
        />
      </motion.div>
      
      <motion.div 
        className={bubbleClass}
        variants={bubbleVariants}
        whileHover="hover"
        onHoverStart={() => !isUser && setShowReactions(true)}
        onHoverEnd={() => setShowReactions(false)}
      >
        {text && (
          <motion.div 
            className={styles.msgText}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            {renderText(text)}
          </motion.div>
        )}
        
        {images && images.map((src, idx) => (
          <motion.div 
            key={idx} 
            className={styles.imageWrapper}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 + idx * 0.1 }}
            whileHover={{ scale: 1.05 }}
          >
            <img src={src} alt="chat-img" className={styles.image} />
          </motion.div>
        ))}
        
        {sources && sources.length > 0 && (
          <motion.div 
            className={styles.sources}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <small>Sources: {sources.join(', ')}</small>
          </motion.div>
        )}
        
        <motion.span 
          className={styles.timestamp}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          {timestamp && new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
        </motion.span>
        
        <span className={tailClass}></span>
        
        {/* Reaction System */}
        {!isUser && (
          <>
            {showReactions && (
              <motion.div 
                className={styles.reactionsPanel}
                initial={{ opacity: 0, scale: 0.8, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.8, y: 10 }}
              >
                {reactions.map((reaction, idx) => (
                  <motion.button
                    key={reaction}
                    className={styles.reactionBtn}
                    onClick={() => handleReaction(reaction)}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: idx * 0.05 }}
                    whileHover={{ scale: 1.2 }}
                    whileTap={{ scale: 0.9 }}
                  >
                    {reaction}
                  </motion.button>
                ))}
              </motion.div>
            )}
            
            {selectedReaction && (
              <motion.div 
                className={styles.selectedReaction}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{ scale: 1.1 }}
              >
                {selectedReaction}
              </motion.div>
            )}
          </>
        )}
      </motion.div>
    </motion.div>
  );
}
