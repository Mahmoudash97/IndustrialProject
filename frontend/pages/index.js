
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




















// import { useState, useRef } from 'react';
// import ChatMessage from '../components/ChatMessage';
// import styles from '../styles/Chat.module.css';

// // You could move the widget-specific CSS to a new module, e.g. ChatWidget.module.css, for clarity.
// const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// export default function Home() {
//   const [showChat, setShowChat] = useState(false);
//   const [messages, setMessages] = useState([]);
//   const [inputText, setInputText] = useState('');
//   const [inputImage, setInputImage] = useState(null);
//   const messagesEndRef = useRef(null);

//   const scrollToBottom = () => {
//     messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     if (!inputText && !inputImage) return;
//     const newUserMsg = {
//       sender: 'user',
//       text: inputText || (inputImage ? '[Image]' : ''),
//       images: inputImage ? [URL.createObjectURL(inputImage)] : []
//     };
//     setMessages(prev => [...prev, newUserMsg]);
//     const formData = new FormData();
//     formData.append('query', inputText);
//     if (inputImage) formData.append('image', inputImage);
//     try {
//       const res = await fetch(`${API_URL}/chat`, { method: 'POST', body: formData });
//       const data = await res.json();
//       const newBotMsg = {
//         sender: 'bot',
//         text: data.message || '',
//         images: []
//       };
//       setMessages(prev => [...prev, newBotMsg]);
//     } catch (err) {
//       setMessages(prev => [...prev, { sender: 'bot', text: 'Error querying backend.', images: [] }]);
//     } finally {
//       setInputText('');
//       setInputImage(null);
//       scrollToBottom();
//     }
//   };

//   return (
//     <div>
//       {/* Your main website content here */}
//       <h1 style={{textAlign: 'center', marginTop: 30}}>Welcome to My Website</h1>
//       <p style={{textAlign: 'center'}}>Explore the site or use the AI chat in the corner!</p>
      
//       {/* Floating chat button */}
//       {!showChat && (
//         <button
//           onClick={() => setShowChat(true)}
//           style={{
//             position: 'fixed',
//             bottom: 30,
//             right: 30,
//             zIndex: 1000,
//             background: '#0084ff',
//             color: '#fff',
//             border: 'none',
//             borderRadius: '50%',
//             width: 60,
//             height: 60,
//             fontSize: 30,
//             boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
//             cursor: 'pointer'
//           }}
//           aria-label="Open Chat"
//         >
//           💬
//         </button>
//       )}

//       {/* Popup chat widget */}
//       {showChat && (
//         <div style={{
//           position: 'fixed',
//           bottom: 100,
//           right: 40,
//           width: 350,
//           height: 500,
//           background: '#fff',
//           borderRadius: 16,
//           boxShadow: '0 6px 32px rgba(0,0,0,0.23)',
//           display: 'flex',
//           flexDirection: 'column',
//           zIndex: 1001,
//           overflow: 'hidden',
//           border: '1px solid #e0e0e0'
//         }}>
//           <div style={{
//             background: '#0084ff',
//             color: '#fff',
//             padding: '10px',
//             fontWeight: 'bold',
//             display: 'flex',
//             justifyContent: 'space-between',
//             alignItems: 'center'
//           }}>
//             <span>AI Chatbot</span>
//             <button
//               onClick={() => setShowChat(false)}
//               style={{
//                 background: 'transparent',
//                 border: 'none',
//                 color: '#fff',
//                 fontSize: 20,
//                 cursor: 'pointer'
//               }}
//               aria-label="Close Chat"
//             >✖</button>
//           </div>
//           <div className={styles.chatHistory} style={{flex: 1, padding: 10, overflowY: 'auto', background: '#f9f9f9'}}>
//             {messages.map((msg, idx) => (
//               <ChatMessage key={idx} sender={msg.sender} text={msg.text} images={msg.images} />
//             ))}
//             <div ref={messagesEndRef} />
//           </div>
//           <form className={styles.inputForm} onSubmit={handleSubmit}>
//             <input 
//               type="text"
//               placeholder="Type your query..."
//               value={inputText}
//               onChange={e => setInputText(e.target.value)}
//               className={styles.textInput}
//             />
//             <input
//               type="file"
//               accept="image/*"
//               onChange={e => setInputImage(e.target.files[0] || null)}
//               className={styles.fileInput}
//             />
//             <button type="submit" className={styles.sendButton}>Send</button>
//           </form>
//         </div>
//       )}
//     </div>
//   );
// }
