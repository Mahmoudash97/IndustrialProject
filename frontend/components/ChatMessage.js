import styles from '../styles/ChatWidget.module.css';

export default function ChatMessage({ sender, text, images, timestamp, avatar, sources, animate }) {
  const isUser = sender === 'user';
  const bubbleClass = isUser ? styles.userBubble : styles.botBubble;
  const containerClass = isUser ? styles.userMsg : styles.botMsg;
  const fadeClass = animate ? styles.fadeIn : '';
  const avatarClass = isUser ? styles.userAvatar : styles.botAvatar;
  const tailClass = isUser ? styles.bubbleTailUser : styles.bubbleTailBot;

  return (
    <div className={`${containerClass} ${fadeClass}`}>
      <div className={avatarClass}>
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
      </div>
      <div className={bubbleClass}>
        {text && <p className={styles.msgText}>{text}</p>}
        {images && images.map((src, idx) => (
          <div key={idx} className={styles.imageWrapper}>
            <img src={src} alt="chat-img" className={styles.image} />
          </div>
        ))}
        {sources && sources.length > 0 && (
          <div className={styles.sources}>
            <small>Sources: {sources.join(', ')}</small>
          </div>
        )}
        <span className={styles.timestamp}>
          {timestamp && new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
        </span>
        <span className={tailClass}></span>
      </div>
    </div>
  );
}
