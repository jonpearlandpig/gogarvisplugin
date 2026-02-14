import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { 
    Send, 
    Trash2, 
    Bot,
    User,
    Terminal,
    Copy,
    Check,
    Upload,
    X,
    File,
    Image,
    FileText,
    Loader2
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const MessageBubble = ({ message, onCopy }) => {
    const [copied, setCopied] = useState(false);
    const isUser = message.role === 'user';

    const handleCopy = () => {
        navigator.clipboard.writeText(message.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`} data-testid={`chat-message-${message.role}`}>
            <div className={`w-8 h-8 border flex items-center justify-center flex-shrink-0 ${
                isUser ? 'border-muted-foreground' : 'border-primary bg-primary/10'
            }`}>
                {isUser ? <User size={14} /> : <Bot size={14} className="text-primary" />}
            </div>
            <div className={`flex-1 max-w-[80%] ${isUser ? 'text-right' : ''}`}>
                <div className={`inline-block p-4 ${
                    isUser 
                        ? 'bg-secondary border border-border' 
                        : 'bg-card border border-primary/30'
                }`}>
                    {/* Show attached files if any */}
                    {message.file_ids && message.file_ids.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-2 pb-2 border-b border-border/50">
                            {message.file_ids.map((fileId, idx) => (
                                <span key={idx} className="inline-flex items-center gap-1 px-2 py-1 bg-background/50 text-xs font-mono">
                                    <File size={10} />
                                    attachment
                                </span>
                            ))}
                        </div>
                    )}
                    <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                        </ReactMarkdown>
                    </div>
                </div>
                <div className="flex items-center gap-2 mt-2 justify-end">
                    <button 
                        className="p-1 text-muted-foreground hover:text-foreground transition-colors"
                        onClick={handleCopy}
                        data-testid="copy-message-btn"
                    >
                        {copied ? <Check size={12} /> : <Copy size={12} />}
                    </button>
                    <span className="font-mono text-[10px] text-muted-foreground">
                        {new Date(message.timestamp).toLocaleTimeString()}
                    </span>
                </div>
            </div>
        </div>
    );
};

const FilePreview = ({ file, onRemove }) => {
    const isImage = file.file_type?.startsWith('image/');
    const Icon = isImage ? Image : FileText;
    
    return (
        <div className="relative group flex items-center gap-2 px-3 py-2 bg-background border border-border" data-testid={`file-preview-${file.file_id}`}>
            <Icon size={16} className={isImage ? "text-green-500" : "text-blue-500"} />
            <div className="flex-1 min-w-0">
                <p className="font-mono text-xs truncate">{file.filename}</p>
                <p className="font-mono text-[10px] text-muted-foreground">
                    {(file.size / 1024).toFixed(1)} KB
                </p>
            </div>
            <button
                onClick={() => onRemove(file.file_id)}
                className="p-1 text-muted-foreground hover:text-destructive transition-colors"
                data-testid={`remove-file-${file.file_id}`}
            >
                <X size={14} />
            </button>
        </div>
    );
};

const DropZone = ({ isDragging, onDrop, onDragOver, onDragLeave, uploading }) => {
    if (!isDragging) return null;
    
    return (
        <div 
            className="absolute inset-0 z-50 bg-background/95 border-2 border-dashed border-primary flex items-center justify-center"
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            data-testid="drop-zone-active"
        >
            <div className="text-center">
                {uploading ? (
                    <>
                        <Loader2 size={48} className="text-primary mx-auto mb-4 animate-spin" />
                        <p className="font-mono text-sm text-primary">UPLOADING FILES...</p>
                    </>
                ) : (
                    <>
                        <Upload size={48} className="text-primary mx-auto mb-4" strokeWidth={1} />
                        <p className="font-mono text-sm text-primary">DROP FILES HERE</p>
                        <p className="font-mono text-[10px] text-muted-foreground mt-2">
                            PNG, JPG, WEBP, PDF, TXT, MD • MAX 50MB
                        </p>
                    </>
                )}
            </div>
        </div>
    );
};

const GarvisChat = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState(() => localStorage.getItem('garvis-session') || null);
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [isDragging, setIsDragging] = useState(false);
    const [uploading, setUploading] = useState(false);
    const scrollRef = useRef(null);
    const inputRef = useRef(null);
    const fileInputRef = useRef(null);
    const dragCounter = useRef(0);

    useEffect(() => {
        if (sessionId) {
            loadHistory();
        }
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    };

    const loadHistory = async () => {
        if (!sessionId) return;
        try {
            const res = await axios.get(`${API}/chat/history/${sessionId}`);
            setMessages(res.data.messages);
        } catch (error) {
            console.error('Error loading history:', error);
        }
    };

    const handleFileUpload = async (files) => {
        const validFiles = Array.from(files).filter(file => {
            const validExtensions = ['.png', '.jpg', '.jpeg', '.webp', '.pdf', '.txt', '.md'];
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            const isValid = validExtensions.includes(ext);
            const isUnderLimit = file.size <= 50 * 1024 * 1024;
            
            if (!isValid) {
                toast.error(`Invalid file type: ${file.name}`);
            }
            if (!isUnderLimit) {
                toast.error(`File too large: ${file.name} (max 50MB)`);
            }
            return isValid && isUnderLimit;
        });

        if (validFiles.length === 0) return;

        setUploading(true);
        const formData = new FormData();
        validFiles.forEach(file => formData.append('files', file));

        try {
            const res = await axios.post(`${API}/chat/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setUploadedFiles(prev => [...prev, ...res.data]);
            toast.success(`${res.data.length} file(s) uploaded`);
        } catch (error) {
            console.error('Upload error:', error);
            toast.error('Failed to upload files');
        } finally {
            setUploading(false);
            setIsDragging(false);
        }
    };

    const removeFile = async (fileId) => {
        try {
            await axios.delete(`${API}/chat/files/${fileId}`);
            setUploadedFiles(prev => prev.filter(f => f.file_id !== fileId));
        } catch (error) {
            console.error('Delete error:', error);
        }
    };

    const handleDragEnter = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter.current++;
        if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
            setIsDragging(true);
        }
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter.current--;
        if (dragCounter.current === 0) {
            setIsDragging(false);
        }
    }, []);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        dragCounter.current = 0;
        
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files);
        }
    }, []);

    const sendMessage = async () => {
        if (!input.trim() || loading) return;

        const fileIds = uploadedFiles.map(f => f.file_id);
        const userMessage = {
            role: 'user',
            content: input,
            file_ids: fileIds,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setUploadedFiles([]); // Clear files after sending
        setLoading(true);

        try {
            const res = await axios.post(`${API}/chat`, {
                message: input,
                session_id: sessionId,
                file_ids: fileIds.length > 0 ? fileIds : null
            });

            const newSessionId = res.data.session_id;
            if (newSessionId !== sessionId) {
                setSessionId(newSessionId);
                localStorage.setItem('garvis-session', newSessionId);
            }

            const assistantMessage = {
                role: 'assistant',
                content: res.data.response,
                timestamp: new Date().toISOString()
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Chat error:', error);
            toast.error('Failed to get response from GARVIS');
            setMessages(prev => prev.slice(0, -1));
        } finally {
            setLoading(false);
            inputRef.current?.focus();
        }
    };

    const clearSession = async () => {
        if (!sessionId) return;
        try {
            await axios.delete(`${API}/chat/session/${sessionId}`);
            setMessages([]);
            setSessionId(null);
            setUploadedFiles([]);
            localStorage.removeItem('garvis-session');
            toast.success('Chat session cleared');
        } catch (error) {
            console.error('Error clearing session:', error);
            toast.error('Failed to clear session');
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div 
            className="space-y-6" 
            data-testid="garvis-chat-page"
            onDragEnter={handleDragEnter}
        >
            {/* Header */}
            <div className="flex items-start justify-between">
                <div className="space-y-2">
                    <h1 className="font-mono text-3xl md:text-4xl font-bold tracking-tighter uppercase">
                        GARVIS AI
                    </h1>
                    <p className="text-muted-foreground font-mono text-sm">
                        Sovereign intelligence assistant powered by GPT-5.2
                    </p>
                </div>
                <button 
                    className="px-4 py-2 border border-border hover:border-destructive hover:text-destructive transition-colors duration-100 font-mono text-xs tracking-wider"
                    onClick={clearSession}
                    disabled={messages.length === 0}
                    data-testid="clear-chat-btn"
                >
                    <Trash2 size={14} className="inline mr-2" />
                    CLEAR
                </button>
            </div>

            {/* Chat Container */}
            <div 
                className="border border-border bg-card relative"
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                {/* Drop Zone Overlay */}
                <DropZone 
                    isDragging={isDragging} 
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    uploading={uploading}
                />

                {/* Terminal Header */}
                <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-background">
                    <Terminal size={14} className="text-primary" />
                    <span className="font-mono text-xs text-muted-foreground">GARVIS TERMINAL</span>
                    <span className="ml-auto font-mono text-[10px] text-muted-foreground">
                        SESSION: {sessionId ? sessionId.slice(0, 8) : 'NEW'}
                    </span>
                </div>

                {/* Messages */}
                <ScrollArea className="h-[400px]" ref={scrollRef}>
                    <div className="p-6 space-y-6">
                        {messages.length === 0 ? (
                            <div className="text-center py-12">
                                <Bot size={48} className="text-primary mx-auto mb-4" strokeWidth={1} />
                                <p className="font-mono text-sm text-muted-foreground mb-2">GARVIS AI READY</p>
                                <p className="text-xs text-muted-foreground max-w-md mx-auto mb-4">
                                    Ask me about the GoGarvis architecture, system components, terminology, 
                                    or any questions about sovereign intelligence and enforcement.
                                </p>
                                <div className="flex items-center justify-center gap-2 text-primary/60">
                                    <Upload size={14} />
                                    <span className="font-mono text-[10px]">DRAG & DROP FILES TO ATTACH</span>
                                </div>
                            </div>
                        ) : (
                            messages.map((msg, idx) => (
                                <MessageBubble key={idx} message={msg} />
                            ))
                        )}
                        {loading && (
                            <div className="flex gap-3">
                                <div className="w-8 h-8 border border-primary bg-primary/10 flex items-center justify-center">
                                    <Bot size={14} className="text-primary" />
                                </div>
                                <div className="bg-card border border-primary/30 p-4">
                                    <span className="font-mono text-sm text-muted-foreground animate-pulse">
                                        PROCESSING<span className="terminal-cursor">_</span>
                                    </span>
                                </div>
                            </div>
                        )}
                    </div>
                </ScrollArea>

                {/* Uploaded Files Preview */}
                {uploadedFiles.length > 0 && (
                    <div className="border-t border-border px-4 py-3 bg-background/50">
                        <div className="flex items-center gap-2 mb-2">
                            <File size={12} className="text-muted-foreground" />
                            <span className="font-mono text-[10px] text-muted-foreground uppercase">
                                {uploadedFiles.length} file(s) attached
                            </span>
                        </div>
                        <div className="flex flex-wrap gap-2" data-testid="uploaded-files-list">
                            {uploadedFiles.map(file => (
                                <FilePreview 
                                    key={file.file_id} 
                                    file={file} 
                                    onRemove={removeFile} 
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* Input */}
                <div className="border-t border-border p-4">
                    <div className="flex gap-4">
                        {/* Hidden file input */}
                        <input
                            type="file"
                            ref={fileInputRef}
                            className="hidden"
                            multiple
                            accept=".png,.jpg,.jpeg,.webp,.pdf,.txt,.md"
                            onChange={(e) => handleFileUpload(e.target.files)}
                            data-testid="file-input"
                        />
                        
                        {/* Upload button */}
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            disabled={uploading}
                            className="px-4 border border-border hover:border-primary hover:text-primary transition-colors duration-100 disabled:opacity-50"
                            title="Upload files"
                            data-testid="upload-btn"
                        >
                            {uploading ? (
                                <Loader2 size={18} className="animate-spin" />
                            ) : (
                                <Upload size={18} />
                            )}
                        </button>
                        
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask GARVIS... (drag & drop files to attach)"
                            rows={2}
                            className="flex-1 bg-background border border-border px-4 py-3 font-mono text-sm resize-none focus:outline-none focus:border-primary"
                            disabled={loading}
                            data-testid="chat-input"
                        />
                        <button
                            onClick={sendMessage}
                            disabled={!input.trim() || loading}
                            className="px-6 bg-primary text-primary-foreground font-mono text-sm tracking-wider uppercase disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors duration-100"
                            data-testid="send-message-btn"
                        >
                            <Send size={18} />
                        </button>
                    </div>
                    <div className="mt-2 font-mono text-[10px] text-muted-foreground flex items-center justify-between">
                        <span>PRESS ENTER TO SEND // SHIFT+ENTER FOR NEW LINE</span>
                        <span className="text-primary/60">PNG, JPG, PDF, TXT, MD • MAX 50MB</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GarvisChat;
