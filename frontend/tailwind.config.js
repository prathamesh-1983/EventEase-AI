/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#4c1d95',
          900: '#2e1065',
        },
      },
      boxShadow: {
        soft: '0 20px 45px rgba(76, 29, 149, 0.12)',
      },
    },
  },
  plugins: [],
}
