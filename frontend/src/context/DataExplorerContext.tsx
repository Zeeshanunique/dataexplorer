'use client';

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { API_BASE_URL } from '@/config/api';

interface DataInfo {
  shape: [number, number];
  columns: string[];
  numeric_columns: string[];
  categorical_columns: string[];
  date_columns: string[];
}

interface ConversationItem {
  user_command: string;
  ai_explanation: string;
  operation_type: string;
  confidence?: number;
  timestamp: string;
  suggestions?: Suggestion[];
}

interface Suggestion {
  type: string;
  description: string;
  operation: Record<string, unknown>;
}

interface RecentSession {
  id: string;
  created_at: string;
  updated_at: string;
  data_info: DataInfo | null;
  conversation_count: number;
}

interface OperationResult {
  operation_type: string;
  operation_params: Record<string, unknown>;
  confidence: number;
  ai_explanation: string;
  suggestions: Suggestion[];
}

interface DataExplorerContextType {
  sessionId: string | null;
  dataInfo: DataInfo | null;
  currentData: Record<string, unknown>[];
  conversationHistory: ConversationItem[];
  operationHistory: Record<string, unknown>[];
  lastOperation: OperationResult | null;
  currentCharts: Record<string, string> | null;
  suggestions: Suggestion[];
  isLoading: boolean;
  isProcessing: boolean;
  isUploading: boolean;
  error: string | null;
  
  // Actions
  createSession: () => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
  processCommand: (command: string) => Promise<void>;
  applySuggestion: (suggestion: Suggestion) => Promise<void>;
  generateChart: (config: Record<string, unknown>) => Promise<Record<string, string> | null>;
  exportData: (format: string) => Promise<void>;
  resetSession: () => Promise<void>;
  clearConversation: () => void;
  clearError: () => void;
  getRecentSessions: () => Promise<RecentSession[]>;
}

const DataExplorerContext = createContext<DataExplorerContextType | undefined>(undefined);

export function DataExplorerProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [dataInfo, setDataInfo] = useState<DataInfo | null>(null);
  const [currentData, setCurrentData] = useState<Record<string, unknown>[]>([]);
  const [conversationHistory, setConversationHistory] = useState<ConversationItem[]>([]);
  const [operationHistory, setOperationHistory] = useState<Record<string, unknown>[]>([]);
  const [lastOperation, setLastOperation] = useState<OperationResult | null>(null);
  const [currentCharts, setCurrentCharts] = useState<Record<string, string> | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Store original data for session recovery
  // Store original data for session recovery (future feature)
  // const [originalData, setOriginalData] = useState<Record<string, unknown>[]>([]);
  // const [originalDataInfo, setOriginalDataInfo] = useState<DataInfo | null>(null);

  const createSession = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to create session');
      }
      
      const data = await response.json();
      setSessionId(data.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Auto-create session on mount
  useEffect(() => {
    if (!sessionId) {
      createSession();
    }
  }, [sessionId, createSession]);

  const uploadFile = useCallback(async (file: File) => {
    let currentSessionId = sessionId;
    
    if (!currentSessionId) {
      console.log('No session available, creating new session...');
      await createSession();
      // Wait for session to be created
      await new Promise(resolve => setTimeout(resolve, 100));
      currentSessionId = sessionId;
      
      if (!currentSessionId) {
        setError('Failed to create session. Please try again.');
        return;
      }
    }

    try {
      setIsUploading(true);
      setError(null);
      
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_BASE_URL}/sessions/${currentSessionId}/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        if (response.status === 404) {
          // Session not found, create a new one and retry
          await createSession();
          const newResponse = await fetch(`${API_BASE_URL}/sessions/${sessionId}/upload`, {
            method: 'POST',
            body: formData,
          });
          if (!newResponse.ok) {
            const errorData = await newResponse.json();
            throw new Error(errorData.detail || 'Failed to upload file');
          }
          // Use the new response
          const data = await newResponse.json();
          setDataInfo({
            shape: data.shape,
            columns: data.columns,
            numeric_columns: Object.keys(data.data_types).filter(col => 
              data.data_types[col].includes('int') || data.data_types[col].includes('float')
            ),
            categorical_columns: Object.keys(data.data_types).filter(col => 
              data.data_types[col].includes('object')
            ),
            date_columns: Object.keys(data.data_types).filter(col => 
              data.data_types[col].includes('datetime')
            ),
          });
          setCurrentData(data.sample_data);
          
          // Load full data
          const dataResponse = await fetch(`${API_BASE_URL}/sessions/${sessionId}/data`);
          if (dataResponse.ok) {
            const dataData = await dataResponse.json();
            setCurrentData(dataData.data);
          }
          return;
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload file');
      }
      
      const data = await response.json();
      setDataInfo({
        shape: data.shape,
        columns: data.columns,
        numeric_columns: Object.keys(data.data_types).filter(col => 
          data.data_types[col].includes('int') || data.data_types[col].includes('float')
        ),
        categorical_columns: Object.keys(data.data_types).filter(col => 
          data.data_types[col].includes('object')
        ),
        date_columns: Object.keys(data.data_types).filter(col => 
          data.data_types[col].includes('datetime')
        ),
      });
      setCurrentData(data.sample_data);
      
      // Load full data
      const dataResponse = await fetch(`${API_BASE_URL}/sessions/${sessionId}/data`);
      if (dataResponse.ok) {
        const dataData = await dataResponse.json();
        setCurrentData(dataData.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  }, [sessionId, createSession]);

  const processCommand = useCallback(async (command: string) => {
    let currentSessionId = sessionId;
    
    if (!currentSessionId) {
      console.log('No session available, creating new session...');
      await createSession();
      // Wait a moment for the session to be created
      await new Promise(resolve => setTimeout(resolve, 100));
      currentSessionId = sessionId;
      
      if (!currentSessionId) {
        setError('Failed to create session. Please try again.');
        return;
      }
    }

    try {
      setIsProcessing(true);
      setError(null);
      
      console.log('Processing command:', command, 'with session:', currentSessionId);
      const response = await fetch(`${API_BASE_URL}/sessions/${currentSessionId}/command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command }),
      });
      
      if (!response.ok) {
        if (response.status === 404) {
          // Session not found, create a new one and retry
          console.log('Session expired, creating new session...');
          await createSession();
          // Wait for session to be created
          await new Promise(resolve => setTimeout(resolve, 100));
          const newSessionId = sessionId;
          
          if (newSessionId) {
            // Retry with new session
            const retryResponse = await fetch(`${API_BASE_URL}/sessions/${newSessionId}/command`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ command }),
            });
            
            if (retryResponse.ok) {
              const retryData = await retryResponse.json();
              console.log('Retry API Response:', retryData);
              
              if (retryData.success) {
                setCurrentData(retryData.data);
                setLastOperation({
                  operation_type: retryData.operation_type,
                  operation_params: retryData.operation_params,
                  confidence: retryData.confidence,
                  ai_explanation: retryData.ai_explanation,
                  suggestions: retryData.suggestions || []
                });
                setSuggestions(retryData.suggestions || []);
                
                // Add to conversation history
                setConversationHistory(prev => [...prev, {
                  user_command: command,
                  ai_explanation: retryData.ai_explanation,
                  timestamp: new Date().toISOString(),
                  operation_type: retryData.operation_type
                }]);
              }
              return;
            }
          }
          
          setError('Session expired. Please upload your data file again to continue the conversation.');
          return;
        } else if (response.status === 400) {
          // No data loaded error
          const errorData = await response.json();
          if (errorData.detail === 'No data loaded') {
            setError('Please upload a CSV file first before making queries. Use the file upload area at the top of the page.');
            return;
          }
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process command');
      }
      
      const data = await response.json();
      console.log('API Response:', data);
      
      if (data.success) {
        setCurrentData(data.data);
        setLastOperation({
          operation_type: data.operation_type,
          operation_params: data.operation_params,
          confidence: data.confidence,
          ai_explanation: data.ai_explanation,
          suggestions: data.suggestions || []
        });
        setSuggestions(data.suggestions || []);
        
        // Update conversation history
        const newConversationItem = {
          user_command: command,
          ai_explanation: data.ai_explanation,
          operation_type: data.operation_type,
          confidence: data.confidence,
          timestamp: new Date().toISOString(),
          suggestions: data.suggestions || []
        };
        console.log('Adding conversation item:', newConversationItem);
        setConversationHistory(prev => {
          const updated = [...prev, newConversationItem];
          console.log('Updated conversation history:', updated);
          return updated;
        });
        
        // Set charts if provided in response
        if (data.charts) {
          setCurrentCharts(data.charts);
        }
        
        // Generate chart if requested via chart_config
        if (data.chart_config) {
          try {
            const chartResponse = await fetch(`${API_BASE_URL}/sessions/${sessionId}/chart`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(data.chart_config),
            });
            
            if (chartResponse.ok) {
              const chartData = await chartResponse.json();
              setCurrentCharts({ [chartData.chart_type || 'bar']: chartData.chart });
            }
          } catch (chartErr) {
            console.warn('Failed to generate chart:', chartErr);
          }
        }
      }
      
    } catch (err) {
      console.error('Error processing command:', err);
      setError(err instanceof Error ? err.message : 'Failed to process command');
    } finally {
      setIsProcessing(false);
    }
  }, [sessionId, createSession]);

  const generateChart = useCallback(async (config: Record<string, unknown>) => {
    if (!sessionId) {
      setError('No session available');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/chart`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate chart');
      }
      
      const data = await response.json();
      return data.charts || { [data.chart_type || 'bar']: data.chart };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate chart');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const exportData = useCallback(async (format: string) => {
    if (!sessionId) {
      setError('No session available');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/export?format=${format}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to export data');
      }
      
      const data = await response.json();
      
      // Create download link
      const blob = new Blob([data.data], { type: data.content_type });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `data_export_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export data');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const resetSession = useCallback(async () => {
    if (!sessionId) {
      setError('No session available');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/reset`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reset session');
      }
      
      // Reload data
      const dataResponse = await fetch(`${API_BASE_URL}/sessions/${sessionId}/data`);
      if (dataResponse.ok) {
        const dataData = await dataResponse.json();
        setCurrentData(dataData.data);
      }
      
      setOperationHistory([]);
      setConversationHistory([]);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset session');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const applySuggestion = useCallback(async (suggestion: Suggestion) => {
    let currentSessionId = sessionId;
    
    if (!currentSessionId) {
      console.log('No session available, creating new session...');
      await createSession();
      // Wait for session to be created
      await new Promise(resolve => setTimeout(resolve, 100));
      currentSessionId = sessionId;
      
      if (!currentSessionId) {
        setError('Failed to create session. Please try again.');
        return;
      }
    }

    try {
      setIsProcessing(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/sessions/${currentSessionId}/apply-suggestion`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ suggestion }),
      });
      
      if (!response.ok) {
        if (response.status === 404) {
          // Session not found, create a new one
          await createSession();
          setError('Session expired. Please upload your data again.');
          return;
        } else if (response.status === 400) {
          // No data loaded error
          const errorData = await response.json();
          if (errorData.detail === 'No data loaded') {
            setError('Please upload a CSV file first before applying suggestions. Use the file upload area at the top of the page.');
            return;
          }
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to apply suggestion');
      }
      
      const data = await response.json();
      
      if (data.success) {
        setCurrentData(data.data);
        setLastOperation({
          operation_type: data.operation_type,
          operation_params: data.operation_params,
          confidence: data.confidence,
          ai_explanation: data.ai_explanation,
          suggestions: data.suggestions || []
        });
        setSuggestions(data.suggestions || []);
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply suggestion');
    } finally {
      setIsProcessing(false);
    }
  }, [sessionId, createSession]);

  const clearConversation = useCallback(() => {
    setConversationHistory([]);
    setLastOperation(null);
    setSuggestions([]);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const getRecentSessions = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/recent`);
      if (response.ok) {
        const data = await response.json();
        return data.sessions;
      }
    } catch (err) {
      console.error('Error fetching recent sessions:', err);
    }
    return [];
  }, []);

  const value: DataExplorerContextType = {
    sessionId,
    dataInfo,
    currentData,
    conversationHistory,
    operationHistory,
    lastOperation,
    currentCharts,
    suggestions,
    isLoading,
    isProcessing,
    isUploading,
    error,
    createSession,
    uploadFile,
    processCommand,
    applySuggestion,
    generateChart,
    exportData,
    resetSession,
    clearConversation,
    clearError,
    getRecentSessions,
  };

  return (
    <DataExplorerContext.Provider value={value}>
      {children}
    </DataExplorerContext.Provider>
  );
}

export function useDataExplorer() {
  const context = useContext(DataExplorerContext);
  if (context === undefined) {
    throw new Error('useDataExplorer must be used within a DataExplorerProvider');
  }
  return context;
}
