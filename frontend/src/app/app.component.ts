import { Component, OnInit, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

type Flow = {
  [key: string]: string | number | null;
  duration: number | null;
  src_bytes: number | null;
  dst_bytes: number | null;
  src_pkts: number | null;
  dst_pkts: number | null;
  proto: string;
  service: string;
  conn_state: string;
  src_port: number | null;
  dst_port: number | null;
  dns_qtype: number | null;
  http_status_code: number | null;
};

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.Eager,
  templateUrl: './app.component.html',
})
export class AppComponent implements OnInit {
  private readonly http = inject(HttpClient);
  readonly staticSite = !['localhost', '127.0.0.1'].includes(window.location.hostname);
  checking = !this.staticSite;
  apiOnline = false;
  ready = false;
  requiredInputs: string[] = [];
  numericInputs: string[] = [];
  busy = false;
  error = '';
  result: {
    predicted_attack_type: string;
    confidence: number;
    class_probabilities: Record<string, number>;
    model_name: string;
    disclaimer: string;
  } | null = null;
  flow: Flow = this.emptyFlow();

  ngOnInit(): void {
    if (this.staticSite) return;
    this.http.get<{ model_ready: boolean }>('/api/health').subscribe({
      next: (health) => {
        this.apiOnline = true;
        this.ready = health.model_ready;
        this.checking = false;
        if (this.ready) this.loadSchema();
      },
      error: () => {
        this.apiOnline = false;
        this.checking = false;
      },
    });
  }

  emptyFlow(): Flow {
    return {
      duration: null, src_bytes: null, dst_bytes: null, src_pkts: null,
      dst_pkts: null, proto: 'tcp', service: '-', conn_state: 'SF',
      src_port: null, dst_port: null, dns_qtype: 0, http_status_code: 0,
    };
  }

  private loadSchema(): void {
    this.http.get<{ required_inputs: string[]; numeric_inputs: string[] }>('/api/schema').subscribe({
      next: (schema) => {
        this.requiredInputs = schema.required_inputs ?? [];
        this.numericInputs = schema.numeric_inputs ?? [];
        for (const field of this.requiredInputs) {
          if (!(field in this.flow)) this.flow[field] = this.numericInputs.includes(field) ? null : '';
        }
      },
      error: () => { this.error = 'The model schema could not be loaded. Restart the local API and check the model bundle.'; },
    });
  }

  get additionalInputs(): string[] {
    const visible = new Set(['duration', 'src_bytes', 'dst_bytes', 'src_pkts', 'dst_pkts', 'proto', 'service', 'conn_state', 'src_port', 'dst_port', 'dns_qtype', 'http_status_code']);
    return this.requiredInputs.filter((field) => !visible.has(field));
  }

  loadExample(): void {
    const example: Flow = {
      duration: 0.042, src_bytes: 1024, dst_bytes: 2048,
      src_pkts: 12, dst_pkts: 18, proto: 'tcp', service: 'http',
      conn_state: 'SF', src_port: 49152, dst_port: 443,
      dns_qtype: 0, http_status_code: 200,
    };
    for (const field of this.requiredInputs) {
      if (!(field in example)) example[field] = this.numericInputs.includes(field) ? null : '';
    }
    this.flow = example;
    this.result = null;
    this.error = '';
  }

  submit(): void {
    this.busy = true;
    this.error = '';
    this.result = null;
    this.http.post<typeof this.result>('/api/predict', this.flow).subscribe({
      next: (result) => {
        this.result = result;
        this.busy = false;
      },
      error: (response) => {
        this.error = response.error?.detail || response.error?.error || 'The local inference service could not be reached.';
        this.busy = false;
      },
    });
  }

  get confidence(): number {
    return this.result ? Math.round(this.result.confidence * 100) : 0;
  }

  get sortedProbabilities(): [string, number][] {
    return Object.entries(this.result?.class_probabilities ?? {}).sort((a, b) => b[1] - a[1]);
  }
}
