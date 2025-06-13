// /frontend/components/ChatWidget.js

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ChatMessage from './ChatMessage';
import VoiceVisualizer from './VoiceVisualizer';
import ImageUploadZone from './ImageUploadZone';
import ParticleBackground from './ParticleBackground';
import styles from '../styles/ChatWidget.module.css';

const BOT_AVATAR = "/bot-avatar.png";
const USER_AVATAR = "/user-avatar.png";

const EMOJIS = ["😀","😂","🥲","😎","😍","🥳","😇","😱","🙏","🔥","🎉","👍","👀","🍕","❤️"];

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [messages, setMessages] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("chat_messages");
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });
  const [inputText, setInputText] = useState("");
  const [inputImages, setInputImages] = useState([]);
  const [isBotTyping, setIsBotTyping] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("chat_darkmode") === "true";
    }
    return false;
  });
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showImageUpload, setShowImageUpload] = useState(false);
  const [typingMessage, setTypingMessage] = useState("");

  const inputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const speechSynthRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isBotTyping]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("chat_messages", JSON.stringify(messages));
    }
  }, [messages]);
  
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("chat_darkmode", darkMode ? "true" : "false");
    }
  }, [darkMode]);

  useEffect(() => {
    if (!minimized && isOpen) {
      setTimeout(() => { inputRef.current?.focus(); }, 200);
    }
  }, [minimized, isOpen, showEmojiPicker]);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === "ArrowUp" && !inputText && messages.length > 0) {
        const lastUserMsg = [...messages].reverse().find(m => (m.sender || m.role) === 'user');
        if (lastUserMsg) {
          const lastText = lastUserMsg.text || lastUserMsg.content || '';
          setInputText(lastText.replace(/ ?\[Image\]$/, ''));
          setEditing(true);
        }
      }
      if (e.key === "Enter" && !e.shiftKey && isOpen && !minimized) {
        if (document.activeElement === inputRef.current) {
          e.preventDefault();
          handleSubmit();
        }
      }
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  });

  const speak = (text) => {
    if (!voiceEnabled || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new window.SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1.02;
    utterance.pitch = 1;
    utterance.volume = 0.8;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    speechSynthRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  const toggleVoice = () => {
    if (isSpeaking) {
      stopSpeaking();
    }
    setVoiceEnabled(!voiceEnabled);
  };

  const playSound = () => {
    if (process.env.NEXT_PUBLIC_ENABLE_SOUND === 'true') {
      const snd = document.getElementById('chatSound');
      if (snd) { 
        snd.currentTime = 0; 
        snd.play().catch(() => {}); 
      }
    }
  };

  const clearChat = () => {
    setMessages([]);
    setInputText('');
    setInputImages([]);
    setEditing(false);
    setError(null);
    stopSpeaking();
    if (typeof window !== 'undefined') {
      localStorage.removeItem('chat_messages');
    }
  };

  const handleMinimize = () => setMinimized(true);
  const handleExpand = () => {
    setMinimized(false);
    setTimeout(() => inputRef.current?.focus(), 150);
  };

  const insertEmoji = (emoji) => {
    setInputText(inputText + emoji);
    setShowEmojiPicker(false);
    inputRef.current?.focus();
  };

  const typewriterEffect = (text, callback) => {
    let i = 0;
    setTypingMessage("");
    const timer = setInterval(() => {
      setTypingMessage(text.slice(0, i));
      i++;
      if (i > text.length) {
        clearInterval(timer);
        setTypingMessage("");
        callback();
      }
    }, 30);
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!inputText && inputImages.length === 0) return;
    
    setLoading(true);
    setIsBotTyping(true);
    setError(null);

    let newMsgs = editing
      ? messages.slice(0, messages.length - 1)
      : [...messages];

    const newUserMsg = {
      sender: 'user',
      text: inputText || (inputImages.length > 0 ? '[Image]' : ''),
      images: inputImages.map(img => URL.createObjectURL(img)),
      timestamp: new Date().toISOString(),
      avatar: USER_AVATAR
    };

    newMsgs = [...newMsgs, newUserMsg];
    setMessages(newMsgs);
    setEditing(false);
    playSound();

    const formData = new FormData();
    formData.append('query', inputText);
    inputImages.forEach((image, index) => {
      formData.append('image', image);
    });

    try {
      const res = await fetch('/api/chat', { 
        method: 'POST', 
        body: formData 
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data = await res.json();
      
      setTimeout(() => {
        const newBotMsg = {
          sender: 'bot',
          text: data.message || data.content || 'I received your message but couldn\'t generate a response.',
          images: [],
          timestamp: new Date().toISOString(),
          avatar: BOT_AVATAR,
          sources: data.sources || [],
          messageId: data.message_id
        };
        
        setMessages(prev => [...prev, newBotMsg]);
        setIsBotTyping(false);
        setLoading(false);
        playSound();
        
        if (voiceEnabled) {
          speak(data.message || data.content || '');
        }
      }, 700);
      
    } catch (err) {
      console.error('Chat error:', err);
      setError(err.message);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: 'I apologize, but I\'m experiencing technical difficulties. Please try again.',
        images: [],
        timestamp: new Date().toISOString(),
        avatar: BOT_AVATAR,
        error: true
      }]);
      setIsBotTyping(false);
      setLoading(false);
      playSound();
    }

    setInputText('');
    setInputImages([]);
  };

  const handleImageUpload = (files) => {
    setInputImages(prev => [...prev, ...files]);
    setShowImageUpload(false);
  };

  const removeImage = (index) => {
    setInputImages(prev => prev.filter((_, i) => i !== index));
  };

  const fabVariants = {
    initial: { scale: 0, rotate: -180 },
    animate: { 
      scale: 1, 
      rotate: 0,
      transition: { type: "spring", stiffness: 260, damping: 20 }
    },
    hover: { 
      scale: 1.1, 
      rotate: 5,
      transition: { type: "spring", stiffness: 400, damping: 10 }
    },
    tap: { scale: 0.95 }
  };

  const widgetVariants = {
    initial: { 
      opacity: 0, 
      scale: 0.8, 
      y: 100,
      rotateX: -15 
    },
    animate: { 
      opacity: 1, 
      scale: 1, 
      y: 0,
      rotateX: 0,
      transition: { 
        type: "spring", 
        stiffness: 260, 
        damping: 20,
        duration: 0.6
      }
    },
    exit: { 
      opacity: 0, 
      scale: 0.8, 
      y: 100,
      transition: { duration: 0.3 }
    }
  };

  // --- NORMALIZE MESSAGES FOR RENDERING ---
  const normalizedMessages = messages.map(msg => ({
    sender: msg.sender || msg.role,
    text: msg.text || msg.content,
    images: msg.images || [],
    timestamp: msg.timestamp || new Date().toISOString(),
    avatar: msg.avatar || (msg.role === 'user' || msg.sender === 'user' ? USER_AVATAR : BOT_AVATAR),
    sources: msg.sources || [],
    messageId: msg.messageId || msg.message_id || undefined
  }));

  // --- RENDER ---
  if (!isOpen) {
    return (
      <>
        <motion.button 
          className={styles.fabChatOpen} 
          onClick={() => setIsOpen(true)} 
          title="Open chat"
          aria-label="Open AI Assistant Chat"
          variants={fabVariants}
          initial="initial"
          animate="animate"
          whileHover="hover"
          whileTap="tap"
        >
          💬
        </motion.button>
        {/* Notification audio with both mp3 and ogg for compatibility */}
        <audio id="chatSound" preload="auto">
          <source src="/static/sounds/notification.mp3" type="audio/mpeg" />
          <source src="/static/sounds/notification.ogg" type="audio/ogg" />
        </audio>
        <ParticleBackground />
      </>
    );
  }

  return (
    <AnimatePresence>
      <motion.div 
        className={`${styles.widgetContainer} ${darkMode ? styles.dark : ''}`}
        variants={widgetVariants}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        {/* Notification audio with both mp3 and ogg for compatibility */}
        <audio id="chatSound" preload="auto">
          <source src="/static/sounds/notification.mp3" type="audio/mpeg" />
          <source src="/static/sounds/notification.ogg" type="audio/ogg" />
        </audio>
        <ParticleBackground />
        
        <motion.div 
          className={styles.header}
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <span style={{display: 'flex', alignItems: 'center'}}>
            <motion.span 
              className={styles.avatar}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              <img src={BOT_AVATAR} alt="bot" width="32" height="32" style={{borderRadius: '50%'}} />
            </motion.span>
            {process.env.NEXT_PUBLIC_APP_NAME || 'AI Assistant'}
          </span>
          <div style={{display:'flex',alignItems:'center',gap:'8px'}}>
            <motion.button 
              className={`${styles.iconBtn} ${voiceEnabled ? styles.voiceEnabled : styles.voiceDisabled}`}
              title={voiceEnabled ? "Voice On" : "Voice Off"}
              onClick={toggleVoice}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              {voiceEnabled ? "🔊" : "🔇"}
            </motion.button>
            {isSpeaking && <VoiceVisualizer />}
            <motion.button 
              className={styles.iconBtn} 
              title="Dark mode" 
              onClick={() => setDarkMode(dm => !dm)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              {darkMode ? "🌙" : "☀️"}
            </motion.button>
            <motion.button 
              className={styles.iconBtn} 
              title="Minimize" 
              onClick={handleMinimize}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              🗕
            </motion.button>
            <motion.button 
              className={styles.iconBtn} 
              title="Clear chat" 
              onClick={clearChat}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              🗑️
            </motion.button>
            <motion.button 
              className={styles.closeButton} 
              onClick={() => setIsOpen(false)} 
              title="Close"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              ✖
            </motion.button>
          </div>
        </motion.div>
        
        {!minimized && (
        <>
          <motion.div 
            className={styles.chatHistory}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            {error && (
              <motion.div 
                className={styles.errorMessage}
                initial={{ opacity: 0, x: -50 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <p>⚠️ Connection Error: {error}</p>
              </motion.div>
            )}
            <AnimatePresence>
              {normalizedMessages.map((msg, idx) => (
                <ChatMessage
                  key={idx}
                  sender={msg.sender}
                  text={msg.text}
                  images={msg.images}
                  timestamp={msg.timestamp}
                  avatar={msg.avatar}
                  sources={msg.sources}
                  animate
                  index={idx}
                />
              ))}
            </AnimatePresence>
            {isBotTyping && (
              <motion.div 
                className={styles.botMsg}
                initial={{ opacity: 0, x: -50 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <div className={styles.botBubble}>
                  <span className={styles.typing}>
                    <span className={styles.dot}></span>
                    <span className={styles.dot}></span>
                    <span className={styles.dot}></span>
                  </span>
                  <span style={{marginLeft: 7}}>
                    {typingMessage || "Assistant is typing..."}
                  </span>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </motion.div>
          
          <motion.form 
            className={styles.inputForm} 
            onSubmit={handleSubmit} 
            autoComplete="off"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            {inputImages.length > 0 && (
              <motion.div 
                className={styles.imagePreview}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
              >
                {inputImages.map((image, index) => (
                  <motion.div 
                    key={index} 
                    className={styles.imagePreviewItem}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                  >
                    <img src={URL.createObjectURL(image)} alt="preview" />
                    <button type="button" onClick={() => removeImage(index)}>×</button>
                  </motion.div>
                ))}
              </motion.div>
            )}
            
            <motion.button 
              type="button"
              className={styles.emojiBtn}
              onClick={() => setShowEmojiPicker(e => !e)}
              tabIndex={-1}
              aria-label="Emoji picker"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              😃
            </motion.button>
            
            <AnimatePresence>
              {showEmojiPicker && (
                <motion.div 
                  className={styles.emojiPicker}
                  initial={{ opacity: 0, scale: 0.8, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.8, y: 10 }}
                >
                  {EMOJIS.map((e,i) => (
                    <motion.button
                      type="button"
                      key={i}
                      className={styles.emoji}
                      onClick={() => insertEmoji(e)}
                      tabIndex={-1}
                      whileHover={{ scale: 1.2 }}
                      whileTap={{ scale: 0.9 }}
                    >
                      {e}
                    </motion.button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
            
            <motion.input 
              type="text"
              placeholder={editing ? "Edit your last message..." : "Type your message..."}
              value={inputText}
              ref={inputRef}
              onChange={e => setInputText(e.target.value)}
              className={styles.textInput}
              autoFocus
              disabled={loading}
              whileFocus={{ scale: 1.02 }}
            />
            
            <motion.button 
              type="button"
              className={styles.imageBtn}
              onClick={() => setShowImageUpload(true)}
              aria-label="Upload Image"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              📎
            </motion.button>
            
            <motion.button 
              type="submit" 
              className={styles.sendButton}
              aria-label="Send"
              disabled={loading || (!inputText && inputImages.length === 0)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              <motion.span 
                className={styles.plane}
                animate={loading ? { rotate: 360 } : {}}
                transition={{ duration: 1, repeat: loading ? Infinity : 0 }}
              >
                <svg height="22" width="22" viewBox="0 0 22 22" fill="none">
                  <path d="M2 11L20 2L11 20L9 13L2 11Z" fill="currentColor" />
                </svg>
              </motion.span>
            </motion.button>
          </motion.form>
          
          <AnimatePresence>
            {showImageUpload && (
              <ImageUploadZone 
                onUpload={handleImageUpload}
                onClose={() => setShowImageUpload(false)}
              />
            )}
          </AnimatePresence>
        </>
        )}
        
        {minimized && (
          <motion.button
            className={styles.expandBtn}
            onClick={handleExpand}
            aria-label="Expand Chat"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            💬
          </motion.button>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
