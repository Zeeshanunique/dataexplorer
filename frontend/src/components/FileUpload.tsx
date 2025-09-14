'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, AlertCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { useDataExplorer } from '@/context/DataExplorerContext';

export default function FileUpload() {
  const { uploadFile, isUploading } = useDataExplorer();
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    setError(null);
    const file = acceptedFiles[0];
    
    try {
      await uploadFile(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    }
  }, [uploadFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    multiple: false
  });

  return (
    <div className="space-y-4">
      <Card 
        {...getRootProps()} 
        className={`cursor-pointer transition-all duration-200 ${
          isDragActive 
            ? 'border-primary bg-primary/5 scale-[1.02]' 
            : 'border-dashed hover:border-primary/50 hover:bg-muted/30'
        }`}
      >
        <CardContent className="p-8 text-center">
          <input {...getInputProps()} />
          <div className={`mx-auto h-16 w-16 mb-4 rounded-full flex items-center justify-center transition-colors ${
            isDragActive ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
          }`}>
            <Upload className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-semibold mb-2">
            {isDragActive ? 'Drop your file here' : 'Upload your data'}
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            {isDragActive
              ? 'Release to upload'
              : 'Drag & drop a file here, or click to browse'}
          </p>
          <div className="flex flex-wrap justify-center gap-2 text-xs text-muted-foreground">
            <Badge variant="outline">CSV</Badge>
            <Badge variant="outline">XLS</Badge>
            <Badge variant="outline">XLSX</Badge>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {isUploading && (
        <div className="flex items-center justify-center space-x-3 p-4 bg-muted/50 rounded-lg">
          <div className="animate-spin rounded-full h-5 w-5 border-2 border-primary border-t-transparent"></div>
          <span className="text-sm font-medium">Processing your file...</span>
        </div>
      )}
    </div>
  );
}