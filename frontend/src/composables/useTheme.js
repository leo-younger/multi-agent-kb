import { ref, watch } from 'vue'

const theme = ref(localStorage.getItem('theme') || 'light')

export function useTheme() {
  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', theme.value)
  }

  watch(theme, (val) => {
    document.documentElement.dataset.theme = val
  }, { immediate: true })

  return { theme, toggleTheme }
}
