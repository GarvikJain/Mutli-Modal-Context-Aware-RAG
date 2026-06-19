import ReactMarkdown from 'react-markdown'
import { motion } from 'framer-motion'
import { User, Sparkles } from 'lucide-react'
import SourceCard from './SourceCard.jsx'
import './MessageBubble.css'

export default function MessageBubble({ message, onCitationClick }) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      className={`message-row ${isUser ? 'is-user' : 'is-assistant'}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <div className="message-avatar">
        {isUser ? <User size={14} /> : <Sparkles size={14} />}
      </div>

      <div className="message-content">
        <div className="message-bubble">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {message.citations?.length > 0 && (
          <div className="message-sources">
            <p className="message-sources-label">Sources used</p>
            <div className="message-sources-list">
              {message.citations.map((c) => (
                <SourceCard
                  key={c.id}
                  citation={c}
                  onClick={() => onCitationClick?.(message.highlightedNodes, c)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
}
