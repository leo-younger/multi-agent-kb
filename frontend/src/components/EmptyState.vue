<template>
  <div class="empty-state">
    <div class="empty-icon">{{ icon }}</div>
    <div class="empty-title">{{ title }}</div>
    <div class="empty-desc" v-if="description">{{ description }}</div>
    <slot name="action"></slot>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: '◇' },
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '' },
})
</script>

<style scoped>
.empty-state {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  font-size: 48px; margin-bottom: 16px;
  opacity: 0.3; line-height: 1; color: var(--text-muted);
}
.empty-title {
  font-family: var(--font-display);
  font-size: 16px; font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.empty-desc {
  font-size: 13px; color: var(--text-muted);
  max-width: 280px; line-height: 1.5;
}
</style>
