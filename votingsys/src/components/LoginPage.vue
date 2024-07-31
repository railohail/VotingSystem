<!-- src/components/LoginPage.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

const username = ref('')
const authStore = useAuthStore()
const router = useRouter()

const login = () => {
  if (username.value.trim()) {
    authStore.login(username.value.trim())
    router.push('/poll')
  }
}
</script>

<template>
  <div class="login-container">
    <h1 class="text-2xl mb-4">Login to access the poll</h1>
    <div class="p-fluid">
      <div class="p-field mb-3">
        <label for="username" class="block mb-2">Enter your name</label>
        <InputText id="username" v-model="username" placeholder="Your name" />
      </div>
      <Button label="Login" @click="login" />
    </div>
  </div>
</template>

<style scoped>
.login-container {
  max-width: 300px;
  margin: 50px auto;
}
</style>