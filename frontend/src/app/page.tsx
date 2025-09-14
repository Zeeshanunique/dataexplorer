'use client';

import { Upload, BarChart3, Send, Bot, User, Trash2, Download as DownloadIcon } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import FileUpload from '@/components/FileUpload';
import { DataExplorerProvider, useDataExplorer } from '@/context/DataExplorerContext';
import { useState, useRef, useEffect } from 'react';

// Chat Message Component
function ChatMessage({ message, isUser, timestamp, suggestions, onSuggestionClick, data }: {
  message: string;
  isUser: boolean;
  timestamp: string;
  suggestions?: Array<{ type: string; description: string; operation: Record<string, unknown> }>;
  onSuggestionClick?: (suggestion: { type: string; description: string; operation: Record<string, unknown> }) => void;
  data?: Record<string, unknown>[];
}) {
  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
          <Bot className="h-4 w-4 text-primary" />
        </div>
      )}
      
      <div className={`max-w-[80%] ${isUser ? 'order-first' : ''}`}>
                    <div className={`rounded-2xl px-4 py-3 ${
                      isUser 
                        ? 'bg-primary text-primary-foreground ml-auto' 
                        : 'bg-muted'
                    }`}>
                      <p className="text-sm whitespace-pre-wrap">{message}</p>
                    </div>
                    
                    {/* Data Display */}
                    {!isUser && data && data.length > 0 && (
                      <div className="mt-3 bg-background border rounded-lg overflow-hidden">
                        <div className="p-3 border-b bg-muted/50">
                          <p className="text-sm font-medium">Results ({data.length} rows)</p>
                        </div>
                        <div className="max-h-96 overflow-auto">
                          <table className="w-full text-sm">
                            <thead className="bg-muted/30 sticky top-0">
                              <tr>
                                {Object.keys(data[0]).slice(0, 8).map((key) => (
                                  <th key={key} className="px-3 py-2 text-left font-medium text-muted-foreground">
                                    {key}
                                  </th>
                                ))}
                                {Object.keys(data[0]).length > 8 && (
                                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">
                                    ...
                                  </th>
                                )}
                              </tr>
                            </thead>
                            <tbody>
                              {data.slice(0, 10).map((row, index) => (
                                <tr key={index} className="border-b hover:bg-muted/20">
                                  {Object.keys(row).slice(0, 8).map((key) => (
                                    <td key={key} className="px-3 py-2 max-w-[200px] truncate" title={String(row[key])}>
                                      {String(row[key])}
                                    </td>
                                  ))}
                                  {Object.keys(row).length > 8 && (
                                    <td className="px-3 py-2 text-muted-foreground">
                                      ...
                                    </td>
                                  )}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {data.length > 10 && (
                            <div className="p-2 text-center text-xs text-muted-foreground border-t">
                              Showing first 10 of {data.length} rows
                            </div>
                          )}
                        </div>
                      </div>
                    )}
        
        {suggestions && suggestions.length > 0 && (
          <div className="mt-3 space-y-2">
            <p className="text-xs text-muted-foreground">Suggestions:</p>
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => onSuggestionClick?.(suggestion)}
                className="block w-full text-left p-3 bg-background border rounded-lg hover:bg-muted/50 transition-colors text-sm"
              >
                <div className="flex items-center justify-between">
                  <span>{suggestion.description}</span>
                  <Badge variant="outline" className="text-xs">
                    {suggestion.type}
                  </Badge>
                </div>
              </button>
            ))}
          </div>
        )}
        
        <p className="text-xs text-muted-foreground mt-2">
          {timestamp}
        </p>
      </div>
      
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}

// Typing Indicator Component
function TypingIndicator() {
  return (
    <div className="flex gap-3 justify-start mb-6">
      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
        <Bot className="h-4 w-4 text-primary" />
      </div>
      <div className="bg-muted rounded-2xl px-4 py-3">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        </div>
      </div>
    </div>
  );
}


// Main App Component - ChatGPT-like Interface
function AppContent() {
  const { 
    dataInfo, 
    currentData,
    conversationHistory, 
    processCommand, 
    isProcessing, 
    applySuggestion,
    resetSession,
    exportData,
    error,
    clearError
  } = useDataExplorer();
  
  console.log('Current conversation history:', conversationHistory);
  
  const [message, setMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Show welcome only when there are no conversation items
  const showWelcome = conversationHistory.length === 0;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversationHistory, isProcessing]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isProcessing) return;
    
    await processCommand(message);
    setMessage('');
  };

  const handleSuggestionClick = async (suggestion: { type: string; description: string; operation: Record<string, unknown> }) => {
    if (suggestion.type === 'command' && suggestion.operation.command) {
      // For command suggestions, set the message and let user send it
      setMessage(suggestion.operation.command as string);
    } else {
      // For other suggestions, apply them directly
      await applySuggestion(suggestion);
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <BarChart3 className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h1 className="text-lg font-semibold">Data Explorer</h1>
                <p className="text-xs text-muted-foreground">AI-Powered Analytics</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {dataInfo && (
                <>
                  <Badge variant="outline" className="text-xs">
                    {dataInfo.shape[0].toLocaleString()} rows
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={resetSession}
                    className="text-xs"
                  >
                    <Trash2 className="h-3 w-3 mr-1" />
                    New Chat
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        {!dataInfo ? (
          // Welcome State
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="text-center max-w-md">
              <div className="p-4 bg-primary/10 rounded-full w-20 h-20 mx-auto mb-6 flex items-center justify-center">
                <Upload className="h-10 w-10 text-primary" />
              </div>
              <h2 className="text-2xl font-bold mb-4">Welcome to Data Explorer</h2>
              <p className="text-muted-foreground mb-8">
                Upload your data file to start exploring with natural language commands
              </p>
              <Card className="max-w-lg mx-auto">
                <CardContent className="p-6">
                  <FileUpload />
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          // Chat Interface
          <div className="flex-1 flex flex-col">
            {/* Messages Area */}
            <ScrollArea className="flex-1 p-6">
              <div className="space-y-6">
                {showWelcome && (
                  <div className="text-center py-8">
                    <div className="p-4 bg-primary/10 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                      <Bot className="h-8 w-8 text-primary" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">Hello! I&apos;m your Data Assistant</h3>
                    <p className="text-muted-foreground mb-6">
                      I can help you analyze your data. Try asking me things like:
                    </p>
                    <div className="grid gap-2 max-w-md mx-auto">
                      <button
                        onClick={() => setMessage("Show me the top 5 products by sales")}
                        className="p-3 text-left bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm"
                      >
                        &quot;Show me the top 5 products by sales&quot;
                      </button>
                      <button
                        onClick={() => setMessage("Group by region and sum revenue")}
                        className="p-3 text-left bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm"
                      >
                        &quot;Group by region and sum revenue&quot;
                      </button>
                      <button
                        onClick={() => setMessage("Create a bar chart of sales by category")}
                        className="p-3 text-left bg-muted rounded-lg hover:bg-muted/80 transition-colors text-sm"
                      >
                        &quot;Create a bar chart of sales by category&quot;
                      </button>
                    </div>
                  </div>
                )}

                {/* Conversation History */}
                {conversationHistory.map((entry, index) => (
                  <div key={index}>
                    <ChatMessage
                      message={entry.user_command}
                      isUser={true}
                      timestamp={formatTime(entry.timestamp)}
                    />
                    <ChatMessage
                      message={entry.ai_explanation}
                      isUser={false}
                      timestamp={formatTime(entry.timestamp)}
                      suggestions={entry.suggestions}
                      onSuggestionClick={handleSuggestionClick}
                      data={index === conversationHistory.length - 1 ? currentData : undefined}
                    />
                  </div>
                ))}

                {/* Typing Indicator */}
                {isProcessing && <TypingIndicator />}
                
                {/* Error Display */}
                {error && (
                  <div className="flex gap-3 justify-start mb-6">
                    <div className="w-8 h-8 rounded-full bg-destructive/10 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-destructive" />
                    </div>
                    <div className="max-w-[80%]">
                      <div className="bg-destructive/10 border border-destructive/20 rounded-2xl px-4 py-3">
                        <p className="text-sm text-destructive mb-3">{error}</p>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={clearError}
                            className="text-xs"
                          >
                            Dismiss
                          </Button>
                          {error.includes('Session expired') && (
                            <Button
                              size="sm"
                              onClick={() => {
                                clearError();
                                // Scroll to top to show upload area
                                window.scrollTo({ top: 0, behavior: 'smooth' });
                              }}
                              className="text-xs"
                            >
                              Upload Data Again
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input Area */}
            <div className="border-t bg-background/95 backdrop-blur-sm p-4">
              <form onSubmit={handleSubmit} className="flex gap-3">
                <div className="flex-1 relative">
                  <Textarea
                    ref={textareaRef}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Ask me anything about your data..."
                    className="min-h-[44px] max-h-32 resize-none pr-12"
                    disabled={isProcessing}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit(e);
                      }
                    }}
                  />
                  <Button
                    type="submit"
                    size="sm"
                    disabled={!message.trim() || isProcessing}
                    className="absolute right-2 bottom-2 h-8 w-8 p-0"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </form>
              
              {/* Quick Actions */}
              {dataInfo && (
                <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground">
                  <div className="flex items-center space-x-4">
                    <span>{dataInfo.shape[0].toLocaleString()} rows • {dataInfo.shape[1]} columns</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => exportData('csv')}
                      className="text-xs h-6"
                    >
                      <DownloadIcon className="h-3 w-3 mr-1" />
                      Export CSV
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function Home() {
  return (
    <DataExplorerProvider>
      <AppContent />
    </DataExplorerProvider>
  );
}