import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  rawFile: File | null = null;
  cleanedText = '';
  analysisReady = false;
  predictionText = '';
  chartInstance: Chart | null = null;
  delimiter = ',';

  constructor(private http: HttpClient) {}

  onRawSelect(e: any) { this.rawFile = e.target.files[0]; }

  async cleanData() {
    if (!this.rawFile) return alert('Please upload a file first');
    const fd = new FormData(); fd.append('file', this.rawFile);
    try {
      await this.http.post('http://localhost:8000/upload', fd, { params: { delimiter: this.delimiter } }).toPromise();
      const res: any = await this.http.post('http://localhost:8000/clean', {}).toPromise();
      this.cleanedText = JSON.stringify(res.data, null, 2);
      this.analysisReady = false;
      this.predictionText = '';
    } catch(e) { alert('Upload/Clean failed'); }
  }

  async uploadCleaned(e: any) {
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData(); fd.append('file', file);
    const res: any = await this.http.post('http://localhost:8000/upload-cleaned', fd, { params: { delimiter: this.delimiter } }).toPromise();
    // Reload cleaned text from backend to sync state
    const cleanRes: any = await this.http.post('http://localhost:8000/clean', {}).toPromise();
    this.cleanedText = JSON.stringify(cleanRes.data, null, 2);
  }

  exportData() {
    const blob = new Blob([this.cleanedText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'cleaned_sales.txt'; a.click();
  }

  async showLineGraph() {
    const res: any = await this.http.post('http://localhost:8000/graph', {}).toPromise();
    if (this.chartInstance) this.chartInstance.destroy();
    this.chartInstance = new Chart('salesChart', {
      type: 'line',
      data: { labels: res.labels, datasets: [{ label: 'Sales Detail', data: res.values, borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,0.1)', tension: 0.3, fill: true }] },
      options: { responsive: true, scales: { y: { beginAtZero: true } } }
    });
  }

  async runAnalysis(type: string) {
    await this.http.post(`http://localhost:8000/analyze/${type}`, {}).toPromise();
    this.analysisReady = true;
  }

  async runPredictions() {
    if (!this.analysisReady) return alert('Run an analysis first');
    const res: any = await this.http.post('http://localhost:8000/predict', {}).toPromise();
    this.predictionText = `📊 TREND: ${res.trend}\n🔮 PREDICTIONS (Next 3 periods): ${res.predictions.join(' | ')}\n\n💡 RECOMMENDATIONS:\n${res.recommendations.map((r: string, i: number) => `${i + 1}. ${r}`).join('\n')}`;
  }
}
