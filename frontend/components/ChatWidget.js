import { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import styles from '../styles/ChatWidget.module.css';
import { v4 as uuidv4 } from 'uuid';

const BOT_AVATAR = "/bot-avatar.png";
const USER_AVATAR = "/user-avatar.png";
const NOTIF_SOUND = "/notification.mp3";

// Use environment variable with fallback
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const EMOJIS = ["😀", "😂", "🥲", "😎", "😍", "🥳", "😇", "😱", "🙏", "🔥", "🎉", "👍", "👀", "🍕", "❤️"];

export default function ChatWidget() {
  const [sessionId, setSessionId] = useState(() => {
    if (typeof window !== "undefined") {
      let saved = localStorage.getItem("chat_session_id");
      if (!saved) {
        saved = uuidv4();
        localStorage.setItem("chat_session_id", saved);
      }
      return saved;
    }
    return uuidv4();
  });

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
  const [inputImage, setInputImage] = useState(null);
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

  const inputRef = useRef(null);
  const messagesEndRef = useRef(null);

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
        const lastUserMsg = [...messages].reverse().find(m => m.sender === 'user');
        if (lastUserMsg) {
          setInputText(lastUserMsg.text.replace(/ ?\[Image\]$/, ''));
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
    if ('speechSynthesis' in window && process.env.NEXT_PUBLIC_ENABLE_SPEECH === 'true') {
      const utter = new window.SpeechSynthesisUtterance(text);
      utter.lang = 'en-US';
      utter.rate = 1.02;
      window.speechSynthesis.speak(utter);
    }
  };

  const playSound = () => {
    if (process.env.NEXT_PUBLIC_ENABLE_SOUND === 'true') {
      const snd = document.getElementById('chatSound');
      if (snd) {
        snd.currentTime = 0;
        snd.play().catch(() => { });
      }
    }
  };

  const clearChat = () => {
    setMessages([]);
    setInputText('');
    setEditing(false);
    setError(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('chat_messages');
      // Generate and store a new session ID
      const newSessionId = uuidv4();
      setSessionId(newSessionId);
      localStorage.setItem("chat_session_id", newSessionId);
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

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!inputText && !inputImage) return;

    setLoading(true);
    setIsBotTyping(true);
    setError(null);

    let newMsgs = editing
      ? messages.slice(0, messages.length - 1)
      : [...messages];

    const newUserMsg = {
      sender: 'user',
      text: inputText || (inputImage ? '[Image]' : ''),
      images: inputImage ? [URL.createObjectURL(inputImage)] : [],
      timestamp: new Date().toISOString(),
      avatar: USER_AVATAR
    };

    newMsgs = [...newMsgs, newUserMsg];
    setMessages(newMsgs);
    setEditing(false);
    playSound();

    const formData = new FormData();
    formData.append('query', inputText);
    formData.append('session_id', sessionId);
    if (inputImage) formData.append('image', inputImage);

    try {
      // Use relative URL which will be proxied by Next.js
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
          text: data.message || 'I received your message but couldn\'t generate a response.',
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
        speak(data.message || '');
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
    setInputImage(null);
  };

  const renderLoading = () => (
    <div className={styles.botMsg}>
      <div className={`${styles.botBubble} ${styles.shimmer}`}></div>
    </div>
  );

  if (!isOpen) {
    return (
      <>
        <button
          className={styles.fabChatOpen}
          onClick={() => setIsOpen(true)}
          title="Open chat"
          aria-label="Open AI Assistant Chat"
        >
          💬
        </button>
        <audio id="chatSound" src={NOTIF_SOUND} preload="auto"></audio>
      </>
    );
  }

  return (
    <div className={`${styles.widgetContainer} ${darkMode ? styles.dark : ''}`}>
      <audio id="chatSound" src={NOTIF_SOUND} preload="auto"></audio>
      <div className={styles.header}>
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <span className={styles.avatar}>
            <img src={BOT_AVATAR} alt="bot" width="32" height="32" style={{ borderRadius: '50%' }} />
          </span>
          {process.env.NEXT_PUBLIC_APP_NAME || 'AI Assistant'}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button className={styles.iconBtn} title="Dark mode" onClick={() => setDarkMode(dm => !dm)}>
            {darkMode ? "🌙" : "☀️"}
          </button>
          <button className={styles.iconBtn} title="Minimize" onClick={handleMinimize}>🗕</button>
          <button className={styles.iconBtn} title="Clear chat" onClick={clearChat}>🗑️</button>
          <button className={styles.closeButton} onClick={() => setIsOpen(false)} title="Close">✖</button>
        </div>
      </div>
      {!minimized && (
        <>
          <div className={styles.chatHistory}>
            {error && (
              <div className={styles.errorMessage}>
                <p>⚠️ Connection Error: {error}</p>
              </div>
            )}
            {messages.map((msg, idx) => (
              <ChatMessage
                key={idx}
                sender={msg.sender}
                text={msg.text}
                images={msg.images}
                timestamp={msg.timestamp}
                avatar={msg.avatar}
                sources={msg.sources}
                animate
              />
            ))}
            {isBotTyping && !loading && (
              <div className={styles.botMsg}>
                <div className={styles.botBubble}>
                  <span className={styles.typing}>
                    <span className={styles.dot}></span>
                    <span className={styles.dot}></span>
                    <span className={styles.dot}></span>
                  </span>
                  <span style={{ marginLeft: 7 }}>Assistant is typing...</span>
                </div>
              </div>
            )}
            {loading && renderLoading()}
            <div ref={messagesEndRef} />
          </div>
          <form className={styles.inputForm} onSubmit={handleSubmit} autoComplete="off">
            <button type="button"
              className={styles.emojiBtn}
              onClick={() => setShowEmojiPicker(e => !e)}
              tabIndex={-1}
              aria-label="Emoji picker"
            >😃</button>
            {showEmojiPicker && (
              <div className={styles.emojiPicker}>
                {EMOJIS.map((e, i) => (
                  <button
                    type="button"
                    key={i}
                    className={styles.emoji}
                    onClick={() => insertEmoji(e)}
                    tabIndex={-1}
                  >{e}</button>
                ))}
              </div>
            )}
            <input
              type="text"
              placeholder={editing ? "Edit your last message..." : "Type your message..."}
              value={inputText}
              ref={inputRef}
              onChange={e => setInputText(e.target.value)}
              className={styles.textInput}
              autoFocus
              disabled={loading}
            />
            <input
              type="file"
              accept="image/*"
              onChange={e => setInputImage(e.target.files[0] || null)}
              className={styles.fileInput}
              disabled={loading}
            />
            <button
              type="submit"
              className={styles.sendButton}
              aria-label="Send"
              disabled={loading || (!inputText && !inputImage)}
            >
              <span className={styles.plane}>
                <svg height="22" width="22" viewBox="0 0 22 22" fill="none">
                  <path d="M2 11L20 2L11 20L9 13L2 11Z" fill="currentColor" />
                </svg>
              </span>
            </button>
          </form>
        </>
      )}
      {minimized && (
        <button
          className={styles.expandBtn}
          onClick={handleExpand}
          aria-label="Expand Chat"
        >
          💬
        </button>
      )}
    </div>
  );
}
