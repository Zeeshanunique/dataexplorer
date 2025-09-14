'use client';

import { BarChart3, PieChart, BarChart, TrendingUp, Table, Download, ArrowLeft, RefreshCw } from 'lucide-react';

// Force dynamic rendering
export const dynamic = 'force-dynamic';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useDataExplorer } from '@/context/DataExplorerContext';
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import dynamicImport from 'next/dynamic';

// Types
interface ChartData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
}

interface DataRow {
  [key: string]: unknown;
  date?: string;
  year?: number;
  quarter?: number;
  month?: number;
  region?: string;
  segment?: string;
  channel?: string;
  product_category?: string;
  product_name?: string;
  sku?: string;
  units_sold?: number;
  unit_price?: number;
  discount_pct?: number;
  gross_revenue?: number;
  cogs?: number;
  tax_pct?: number;
  tax_amount?: number;
  returned_units?: number;
  net_revenue?: number;
}

interface DataInfo {
  shape: [number, number];
  numeric_columns: string[];
  categorical_columns: string[];
}

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamicImport(() => import('react-plotly.js'), { ssr: false }) as React.ComponentType<{
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
  style: React.CSSProperties;
  config: Record<string, unknown>;
  useResizeHandler: boolean;
}>;

// Chart Component
function ChartComponent({ 
  type, 
  title, 
  data, 
  dataInfo 
}: { 
  type: string; 
  title: string; 
  data: DataRow[]; 
  dataInfo: DataInfo | null; 
}) {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(false);

  const generateChartData = useCallback(() => {
    try {
      let plotData: Plotly.Data[] = [];
      let layout: Partial<Plotly.Layout> = {};

      switch (type) {
        case 'revenue-trend':
          const revenueData = data.map((row: DataRow) => ({
            date: new Date(row.date || ''),
            revenue: (row.gross_revenue as number) || 0
          })).sort((a, b) => a.date.getTime() - b.date.getTime());

          plotData = [{
            x: revenueData.map(d => d.date),
            y: revenueData.map(d => d.revenue),
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Revenue',
            line: { color: '#3b82f6' }
          }];

          layout = {
            title: { text: 'Revenue Trend Over Time' },
            xaxis: { title: { text: 'Date' } },
            yaxis: { title: { text: 'Revenue ($)' } },
            hovermode: 'closest'
          };
          break;

        case 'region-sales':
          const regionData = data.reduce((acc: Record<string, number>, row: DataRow) => {
            const region = (row.region as string) || 'Unknown';
            acc[region] = (acc[region] || 0) + ((row.gross_revenue as number) || 0);
            return acc;
          }, {});

          plotData = [{
            x: Object.keys(regionData),
            y: Object.values(regionData),
            type: 'bar',
            marker: { color: '#10b981' }
          }];

          layout = {
            title: { text: 'Sales by Region' },
            xaxis: { title: { text: 'Region' } },
            yaxis: { title: { text: 'Total Revenue ($)' } }
          };
          break;

        case 'product-category':
          const categoryData = data.reduce((acc: Record<string, number>, row: DataRow) => {
            const category = (row.product_category as string) || 'Unknown';
            acc[category] = (acc[category] || 0) + ((row.gross_revenue as number) || 0);
            return acc;
          }, {});

          plotData = [{
            labels: Object.keys(categoryData),
            values: Object.values(categoryData),
            type: 'pie',
            textinfo: 'label+percent',
            textposition: 'outside'
          }];

          layout = {
            title: { text: 'Revenue by Product Category' },
            showlegend: true
          };
          break;

        case 'quarterly-performance':
          const quarterlyData = data.reduce((acc: Record<string, Record<string, number>>, row: DataRow) => {
            const quarter = `Q${row.quarter} ${row.year}`;
            const region = (row.region as string) || 'Unknown';
            if (!acc[quarter]) acc[quarter] = {};
            acc[quarter][region] = (acc[quarter][region] || 0) + ((row.gross_revenue as number) || 0);
            return acc;
          }, {});

          const quarters = Object.keys(quarterlyData).sort();
          const regions = [...new Set(data.map((row: DataRow) => row.region).filter(Boolean))] as string[];

          plotData = regions.map(region => ({
            x: quarters,
            y: quarters.map(q => quarterlyData[q][region] || 0),
            type: 'bar',
            name: region
          }));

          layout = {
            title: { text: 'Quarterly Performance by Region' },
            xaxis: { title: { text: 'Quarter' } },
            yaxis: { title: { text: 'Revenue ($)' } },
            barmode: 'group'
          };
          break;

        case 'top-products':
          const productData = data.reduce((acc: Record<string, number>, row: DataRow) => {
            const product = (row.product_name as string) || 'Unknown';
            acc[product] = (acc[product] || 0) + ((row.gross_revenue as number) || 0);
            return acc;
          }, {});

          const sortedProducts = Object.entries(productData)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10);

          plotData = [{
            x: sortedProducts.map(([,value]) => value),
            y: sortedProducts.map(([name]) => name),
            type: 'bar',
            orientation: 'h',
            marker: { color: '#f59e0b' }
          }];

          layout = {
            title: { text: 'Top 10 Products by Revenue' },
            xaxis: { title: { text: 'Revenue ($)' } },
            yaxis: { title: { text: 'Product' } }
          };
          break;

        case 'discount-analysis':
          const discountData = data.map((row: DataRow) => ({
            discount: ((row.discount_pct as number) || 0) * 100,
            revenue: (row.gross_revenue as number) || 0
          }));

          plotData = [{
            x: discountData.map(d => d.discount),
            y: discountData.map(d => d.revenue),
            type: 'scatter',
            mode: 'markers',
            marker: { 
              color: '#ef4444',
              size: 8,
              opacity: 0.6
            }
          }];

          layout = {
            title: { text: 'Discount vs Revenue Analysis' },
            xaxis: { title: { text: 'Discount Percentage (%)' } },
            yaxis: { title: { text: 'Revenue ($)' } }
          };
          break;

        default:
          setLoading(false);
          return;
      }

      setChartData({ data: plotData, layout });
      setLoading(false);
    } catch (error) {
      console.error('Error generating chart data:', error);
      setLoading(false);
    }
  }, [data, type]);

  useEffect(() => {
    if (data.length === 0 || !dataInfo) return;
    
    setLoading(true);
    generateChartData();
  }, [data, dataInfo, type, generateChartData]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">Generating chart...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!chartData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">No data available</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          {title}
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const link = document.createElement('a');
              link.href = `data:image/png;base64,${btoa(JSON.stringify(chartData))}`;
              link.download = `${title.toLowerCase().replace(/\s+/g, '-')}.json`;
              link.click();
            }}
          >
            <Download className="h-4 w-4 mr-1" />
            Export
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <Plot
            data={chartData.data}
            layout={chartData.layout}
            style={{ width: '100%', height: '100%' }}
            config={{ responsive: true, displayModeBar: true }}
            useResizeHandler={true}
          />
        </div>
      </CardContent>
    </Card>
  );
}

// Data Table Component
function DataTable({ data, title }: { data: DataRow[]; title: string }) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="text-muted-foreground">No data available</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const columns = Object.keys(data[0]);
  const displayData = data.slice(0, 100); // Show first 100 rows

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          {title}
          <Badge variant="outline">
            {data.length} rows
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  {columns.map((col) => (
                    <th key={col} className="text-left p-2 font-medium">
                      {col.replace(/_/g, ' ').toUpperCase()}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {displayData.map((row, index) => (
                  <tr key={index} className="border-b hover:bg-muted/50">
                    {columns.map((col) => (
                      <td key={col} className="p-2">
                        {typeof row[col] === 'number' 
                          ? (row[col] as number).toLocaleString()
                          : String(row[col] || '')
                        }
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.length > 100 && (
            <div className="text-center mt-2 text-sm text-muted-foreground">
              Showing first 100 of {data.length} rows
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// Main Visualizations Component
function VisualizationsContent() {
  const { dataInfo, currentData, exportData } = useDataExplorer();
  const [selectedTab, setSelectedTab] = useState('overview');

  if (!dataInfo) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center max-w-md">
          <BarChart3 className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h1 className="text-2xl font-bold mb-2">No Data Available</h1>
          <p className="text-muted-foreground mb-6">
            Please upload a CSV file to view visualizations
          </p>
          <Link href="/">
            <Button>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go to Chat
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'trends', label: 'Trends', icon: TrendingUp },
    { id: 'distribution', label: 'Distribution', icon: PieChart },
    { id: 'comparison', label: 'Comparison', icon: BarChart },
    { id: 'data', label: 'Data Table', icon: Table }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur-sm sticky top-0 z-40">
        <div className="px-4 py-3">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <Link href="/">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Chat
                </Button>
              </Link>
              <div className="p-2 bg-primary/10 rounded-lg">
                <BarChart3 className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h1 className="text-lg font-semibold">Data Visualizations</h1>
                <p className="text-xs text-muted-foreground">
                  {dataInfo.shape[0].toLocaleString()} rows • {dataInfo.shape[1]} columns
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => exportData('csv')}
              >
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="border-b">
        <div className="px-4">
          <div className="flex space-x-1 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <Button
                  key={tab.id}
                  variant={selectedTab === tab.id ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setSelectedTab(tab.id)}
                  className="whitespace-nowrap"
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {tab.label}
                </Button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="p-6">
        <div className="max-w-7xl mx-auto">
          {selectedTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartComponent
                type="revenue-trend"
                title="Revenue Trend"
                data={currentData}
                dataInfo={dataInfo}
              />
              <ChartComponent
                type="region-sales"
                title="Sales by Region"
                data={currentData}
                dataInfo={dataInfo}
              />
              <ChartComponent
                type="product-category"
                title="Revenue by Category"
                data={currentData}
                dataInfo={dataInfo}
              />
              <ChartComponent
                type="top-products"
                title="Top Products"
                data={currentData}
                dataInfo={dataInfo}
              />
            </div>
          )}

          {selectedTab === 'trends' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartComponent
                type="revenue-trend"
                title="Revenue Over Time"
                data={currentData}
                dataInfo={dataInfo}
              />
              <ChartComponent
                type="quarterly-performance"
                title="Quarterly Performance"
                data={currentData}
                dataInfo={dataInfo}
              />
              <ChartComponent
                type="discount-analysis"
                title="Discount Analysis"
                data={currentData}
                dataInfo={dataInfo}
              />
            </div>
          )}

          {selectedTab === 'distribution' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartComponent
                type="product-category"
                title="Product Category Distribution"
                data={currentData}
                dataInfo={dataInfo}
              />
              <ChartComponent
                type="region-sales"
                title="Regional Distribution"
                data={currentData}
                dataInfo={dataInfo}
              />
            </div>
          )}

          {selectedTab === 'comparison' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartComponent
                type="quarterly-performance"
                title="Regional Comparison"
                data={currentData}
                dataInfo={dataInfo}
              />
              <ChartComponent
                type="top-products"
                title="Product Performance"
                data={currentData}
                dataInfo={dataInfo}
              />
            </div>
          )}

          {selectedTab === 'data' && (
            <div className="space-y-6">
              <DataTable
                data={currentData}
                title="Complete Dataset"
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function VisualizationsPage() {
  return <VisualizationsContent />;
}
