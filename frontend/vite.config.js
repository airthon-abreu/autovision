import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,         // Fixa a porta
    strictPort: true    // Impede o Vite de procurar outra porta se essa falhar
  }
})