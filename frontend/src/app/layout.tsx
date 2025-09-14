import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { DataExplorerProvider } from '@/context/DataExplorerContext';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Data Explorer - AI-Powered Analytics',
  description: 'Chat with your data using natural language commands and explore insights with interactive visualizations.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <DataExplorerProvider>
          {children}
        </DataExplorerProvider>
      </body>
    </html>
  );
}