// /frontend/components/ChatMessage.js
import { useState } from 'react';
import { motion } from 'framer-motion';
import styles from '../styles/ChatWidget.module.css';

function getTextContent(text) {
  if (typeof text === 'string') return text;
  if (Array.isArray(text)) {
    return text.map(getTextContent).join(' ');
  }
  if (typeof text === 'object' && text !== null) {
    if ('content' in text) return String(text.content);
    return JSON.stringify(text);
  }
  return '';
}

export default function ChatMessage({ 
  sender, 
  text, 
  images, 
  timestamp, 
  avatar, 
  sources, 
  locations, 
  animate, 
  index 
}) {
  const isUser = sender === 'user';
  const [showReactions, setShowReactions] = useState(false);
  const [selectedReaction, setSelectedReaction] = useState(null);
  const [expandedLocation, setExpandedLocation] = useState(null);
  
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

  const renderText = (rawText) => {
    const safeText = getTextContent(rawText);
    return safeText;
  };

  const handleReaction = (reaction) => {
    setSelectedReaction(reaction);
    setShowReactions(false);
  };

  const renderLocationCards = () => {
    if (!locations || locations.length === 0) return null;

    return (
      <motion.div 
        className={styles.locationResults}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h4>Found Locations:</h4>
        <div className={styles.locationGrid}>
          {locations.map((location, idx) => (
            <motion.div
              key={location.id}
              className={styles.locationCard}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 + idx * 0.1 }}
              whileHover={{ scale: 1.03 }}
              onClick={() => setExpandedLocation(expandedLocation === location.id ? null : location.id)}
            >
              <div className={styles.locationHeader}>
                <h5>{location.location}</h5>
                <span className={styles.similarity}>
                  {Math.round(location.score * 100)}% match
                </span>
              </div>
              <p className={styles.locationDescription}>
                {location.description}
              </p>
              {location.features && location.features.length > 0 && (
                <div className={styles.features}>
                  {location.features.slice(0, 3).map((feature, featureIdx) => (
                    <span key={featureIdx} className={styles.featureTag}>
                      {feature}
                    </span>
                  ))}
                </div>
              )}
              {expandedLocation === location.id && (
                <motion.div 
                  className={styles.expandedDetails}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                >
                  <p><strong>Image Path:</strong> {location.image_path}</p>
                  <p><strong>All Features:</strong> {location.features.join(', ')}</p>
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </motion.div>
    );
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

        {renderLocationCards()}
        
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
