import http from 'k6/http';
import { check, sleep } from 'k6';

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || '5cy_test_key';

export const options = {
  stages: [
    { duration: '30s', target: 20 },    // Ramp up to 20 users over 30s
    { duration: '1m30s', target: 20 },  // Stay at 20 users for 90s
    { duration: '30s', target: 0 },     // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],   // 95% of requests must complete under 500ms
    http_req_failed: ['rate<0.1'],      // error rate must be < 10%
  },
};

// Test data
const endpoints = [
  { path: '/health', method: 'GET', skill: 'health' },
  { path: '/tcg/price?card=Black+Lotus&game=mtg', method: 'GET', skill: 'tcg' },
  { path: '/osha/trades', method: 'GET', skill: 'osha' },
  { path: '/contracts/categories', method: 'GET', skill: 'contracts' },
  { path: '/onboarding/industries', method: 'GET', skill: 'onboarding' },
];

export default function () {
  // Randomly select an endpoint
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  
  const params = {
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    },
  };

  let response;
  
  if (endpoint.method === 'GET') {
    response = http.get(`${BASE_URL}${endpoint.path}`, params);
  } else {
    response = http.post(`${BASE_URL}${endpoint.path}`, {}, params);
  }

  // Validate response
  const result = check(response, {
    'status is 200 or 429': (r) => r.status === 200 || r.status === 429,
    'has ok field': (r) => r.body.includes('"ok"'),
    'has request id': (r) => r.headers['X-Request-ID'] !== undefined,
    'response time < 1s': (r) => r.timings.duration < 1000,
  });

  if (!result) {
    console.error(`Failed: ${endpoint.skill} - Status ${response.status}`);
  }

  // Sleep between requests (0.1-0.5s)
  sleep(Math.random() * 0.4 + 0.1);
}
