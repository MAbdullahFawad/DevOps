import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

type Flow = { duration: number | null; src_bytes: number | null; dst_bytes: number | null; src_pkts: number | null; dst_pkts: number | null; src_port: number | null; dst_port: number | null; proto: string; service: string; conn_state: string; dns_qtype: number | null; http_status_code: number | null };

@Component({ selector: 'app-root', standalone: true, imports: [CommonModule, FormsModule], templateUrl: './app.component.html' })
export class AppComponent implements OnInit {
  private http = inject(HttpClient);
  staticSite = !['localhost', '127.0.0.1'].includes(window.location.hostname);
  ready = false;
  checking = true;
  busy = false;
  error = '';
  result: any = null;
  flow: Flow = { duration: null, src_bytes: null, dst_bytes: null, src_pkts: null, dst_pkts: null, src_port: null, dst_port: null, proto: 'tcp', service: '-', conn_state: 'SF', dns_qtype: 0, http_status_code: 0 };
  ngOnInit() {
    if (this.staticSite) { this.checking = false; return; }
    this.http.get<any>('/api/health').subscribe({ next: r => { this.ready = !!r.model_ready; this.checking = false; }, error: () => { this.checking = false; } });
  }
  submit() {
    this.busy = true; this.error = ''; this.result = null;
    this.http.post<any>('/api/predict', this.flow).subscribe({ next: r => { this.result = r; this.busy = false; }, error: e => { this.error = e.error?.detail || e.error?.error || 'Could not reach the local inference service.'; this.busy = false; } });
  }
  get confidence() { return this.result ? Math.round(this.result.confidence * 100) : 0; }
}
