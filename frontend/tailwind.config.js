/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', '"IBM Plex Mono"', "ui-monospace", "monospace"],
        display: ['"Space Grotesk"', "system-ui", "sans-serif"],
      },
      colors: {
        bg: "#0a0a0b",
        panel: "#111114",
        panel2: "#16161a",
        border: "#26262c",
        text: "#e6e6e8",
        muted: "#7a7a82",
        accent: "#d4ff5e",
        bull: "#4ade80",
        bear: "#f87171",
      },
    },
  },
  plugins: [],
};
