<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import Drawer from 'primevue/drawer'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import { config } from '@/config'

const visible = ref(false)
const newOptionText = ref('')
const newSubjectText = ref('')
const userVotes = ref<{ [subject: string]: string[] }>({})
const router = useRouter()
const authStore = useAuthStore()
const isAddingSubject = ref(false)
const toast = useToast()

const props = defineProps<{
  subject: string
}>()

const emit = defineEmits(['subjectAdded', 'subjectsUpdated'])

interface Option {
  id: number
  text: string
  votes: number
}

const localOptions = ref<Option[]>([])
const allSubjects = ref<string[]>([])
let ws: WebSocket | null = null

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
  } else {
    await fetchInitialPollData()
    connectWebSocket()
  }
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})

watch(
  () => props.subject,
  (newSubject) => {
    if (newSubject) {
      const pollData = JSON.parse(localStorage.getItem('pollData') || '{}')
      updateOptionsForSubject(newSubject, pollData)
    }
  },
  { immediate: true }
)
const handleWebSocketMessage = (event: MessageEvent) => {
  try {
    const data = JSON.parse(event.data)
    if (data.subjects) {
      localStorage.setItem('pollData', JSON.stringify(data)) // Update localStorage
      updateAllSubjects(data)
      updateOptionsForSubject(props.subject, data)
    }
  } catch (error) {
    console.error('Error processing WebSocket message:', error)
  }
}
const connectWebSocket = () => {
  ws = new WebSocket(config.wsUrl)

  ws.onopen = () => {
    console.log('WebSocket connected')
  }

  ws.onmessage = handleWebSocketMessage

  ws.onclose = () => {
    console.log('WebSocket disconnected. Attempting to reconnect...')
    setTimeout(connectWebSocket, 1000)
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
}

const updateAllSubjects = (data: any) => {
  allSubjects.value = Object.keys(data.subjects)
  emit('subjectsUpdated', allSubjects.value)
}

const updateOptionsForSubject = (subject: string, data?: any) => {
  const pollData = data || JSON.parse(localStorage.getItem('pollData') || '{}')
  if (pollData.subjects && pollData.subjects[subject]) {
    localOptions.value = Object.entries(pollData.subjects[subject].options).map(
      ([text, votes], index) => ({
        id: index + 1,
        text,
        votes: votes as number
      })
    )
    if (authStore.user) {
      userVotes.value[subject] = pollData.subjects[subject].votes[authStore.user] || []
    }
  } else {
    localOptions.value = []
    userVotes.value[subject] = []
  }
}

const fetchInitialPollData = async () => {
  try {
    const response = await fetch(`${config.apiUrl}/poll_data`)
    const data = await response.json()
    localStorage.setItem('pollData', JSON.stringify(data))
    updateAllSubjects(data)
    updateOptionsForSubject(props.subject, data)
  } catch (error) {
    console.error('Failed to fetch initial poll data:', error)
  }
}

const totalVotes = computed(() => localOptions.value.reduce((sum, option) => sum + option.votes, 0))

const sortedOptions = computed(() => {
  return [...localOptions.value].sort((a, b) => b.votes - a.votes)
})

const getPercentage = (votes: number) => {
  return totalVotes.value > 0 ? (votes / totalVotes.value) * 100 : 0
}

const vote = (optionText: string) => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.warn('WebSocket is not open. Unable to send vote.')
    return
  }

  const subjectVotes = userVotes.value[props.subject] || []
  const voteIndex = subjectVotes.indexOf(optionText)
  if (voteIndex !== -1) {
    subjectVotes.splice(voteIndex, 1)
  } else if (subjectVotes.length < 2) {
    subjectVotes.push(optionText)
  } else {
    subjectVotes.shift()
    subjectVotes.push(optionText)
  }
  userVotes.value[props.subject] = subjectVotes

  try {
    ws.send(
      JSON.stringify({
        type: 'vote',
        subject: props.subject,
        option: optionText,
        username: authStore.user
      })
    )
  } catch (error) {
    console.error('Error sending vote:', error)
    // Optionally, you could add a toast notification here to inform the user
  }
}

const addNewOption = () => {
  if (!props.subject) {
    toast.add({
      severity: 'warn',
      summary: 'No Subject Selected',
      detail: 'Please select a subject before adding an option.',
      life: 3000
    })
    visible.value = false
    return
  }
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.warn('WebSocket is not open. Unable to add new option.')
    return
  }

  if (newOptionText.value.trim()) {
    try {
      ws.send(
        JSON.stringify({
          type: 'new_option',
          subject: props.subject,
          option: newOptionText.value.trim()
        })
      )
      newOptionText.value = ''
      visible.value = false
    } catch (error) {
      console.error('Error adding new option:', error)
      // Optionally, add a toast notification here
    }
  }
}
const addNewSubject = () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.warn('WebSocket is not open. Unable to add new subject.')
    return
  }

  if (newSubjectText.value.trim()) {
    try {
      ws.send(
        JSON.stringify({
          type: 'new_subject',
          subject: newSubjectText.value.trim()
        })
      )
      emit('subjectAdded', newSubjectText.value.trim())
      newSubjectText.value = ''
      visible.value = false
    } catch (error) {
      console.error('Error adding new subject:', error)
      // Optionally, add a toast notification here
    }
  }
}

const openDrawerForOption = () => {
  if (!props.subject) {
    toast.add({
      severity: 'warn',
      summary: '還未有題目',
      detail: '請先增加題目',
      life: 3000
    })
    return
  }
  visible.value = true
  isAddingSubject.value = false
}

const openDrawerForSubject = () => {
  visible.value = true
  isAddingSubject.value = true
}
</script>

<template>
  <div class="poll-container">
    <Toast
      position="bottom-right"
      :pt="{
        root: {
          class: 'w-64 text-sm !right-0 !bottom-0'
        }
      }"
    />
    <Drawer v-model:visible="visible" :header="isAddingSubject ? '增加題目' : '增加選項'">
      <div class="p-fluid">
        <div v-if="isAddingSubject" class="p-field">
          <InputText id="newSubject" v-model="newSubjectText" placeholder="輸入題目" />
        </div>
        <div v-else class="p-field">
          <InputText id="newOption" v-model="newOptionText" placeholder="輸入選項" />
        </div>
        <Button
          :label="isAddingSubject ? '新增題目' : '新增選項'"
          @click="isAddingSubject ? addNewSubject() : addNewOption()"
          class="mt-3"
        />
      </div>
    </Drawer>

    <div class="header-container">
      <Button
        icon="pi pi-plus"
        label="增加選項"
        rounded
        outlined
        @click="openDrawerForOption"
        class="drawer-button"
      />
      <h1 class="text-white-500 text-2xl">{{ subject || '沒有題目' }}</h1>
      <Button
        rounded
        outlined
        icon="pi pi-list"
        label="增加題目"
        @click="openDrawerForSubject"
        class="drawer-button"
      />
    </div>

    <p class="text-sm text-slate-500 mb-4">可以選至兩個選項，重複點選將會移除該選項。</p>

    <TransitionGroup name="poll-list" tag="div">
      <div
        v-for="option in sortedOptions"
        :key="option.id"
        class="poll-option"
        @click="vote(option.text)"
        :class="{ 'user-voted': userVotes[subject]?.includes(option.text) }"
      >
        <div class="poll-bar" :style="{ width: `${getPercentage(option.votes)}%` }"></div>
        <span class="option-text text-slate-600">{{ option.text }}</span>
        <span class="vote-info">
          <span class="vote-percentage text-slate-600">
            {{ getPercentage(option.votes).toFixed(1) }}%
          </span>
          <span class="vote-count">({{ option.votes.toLocaleString() }})</span>
        </span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.poll-container {
  font-family: Arial, sans-serif;
  max-width: 400px;
  margin: 0 auto;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.poll-option {
  position: relative;
  background-color: #ffffff;
  height: 40px;
  margin-bottom: 10px;
  cursor: pointer;
  overflow: hidden;
  border-radius: 20px;
}

.poll-bar {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background-color: var(--p-emerald-400);
  z-index: 1;
  transition: width 0.3s ease;
  opacity: 0.9;
}

.option-text,
.vote-info {
  position: relative;
  z-index: 2;
  line-height: 40px;
  padding: 0 10px;
}

.option-text {
  float: left;
  font-weight: bold;
}

.vote-info {
  float: right;
  font-size: 0.9em;
}

.vote-percentage {
  font-weight: bold;
  margin-right: 5px;
}

.vote-count {
  color: #666;
}

.poll-list-move {
  transition: transform 0.5s ease;
}

.poll-list-enter-active,
.poll-list-leave-active {
  transition: all 0.5s ease;
}

.poll-list-enter-from,
.poll-list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}

.user-voted {
  border: 2px solid var(--p-emerald-400);
}
</style>
