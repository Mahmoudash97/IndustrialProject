import styles from '../styles/ChatWidget.module.css';

export default function ChatMessage({ sender, text, images, timestamp, avatar, animate }) {
  const isUser = sender === 'user';
  const bubbleClass = isUser ? styles.userBubble : styles.botBubble;
  const containerClass = isUser ? styles.userMsg : styles.botMsg;
  const fadeClass = animate ? styles.fadeIn : '';

  return (
    <div className={`${containerClass} ${fadeClass}`}>
      <div className={isUser ? styles.userAvatar : styles.botAvatar}>
        <img src={avatar} alt={`${sender} avatar`} width="32" height="32" style={{borderRadius: '50%'}} />
      </div>
      <div className={bubbleClass}>
        {text && <p className={styles.msgText}>{text}</p>}
        {images && images.map((src, idx) => (
          <div key={idx} className={styles.imageWrapper}>
            <img src={src} alt="chat-img" className={styles.image} />
          </div>
        ))}
        <span className={styles.timestamp}>
          {timestamp && new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
        </span>
        <span className={isUser ? styles.bubbleTailUser : styles.bubbleTailBot}></span>
      </div>
    </div>
  );
}
