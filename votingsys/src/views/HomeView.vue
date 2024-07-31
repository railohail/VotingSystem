<script setup lang="ts">
import { ref } from 'vue'
import PollComponent from '@/components/pollComponent.vue'

const currentSubject = ref('')
const allSubjects = ref<string[]>([])

const handleSubjectAdded = (newSubject: string) => {
  allSubjects.value.push(newSubject)
  currentSubject.value = newSubject
}

const handleSubjectsUpdated = (subjects: string[]) => {
  allSubjects.value = subjects
  if (!currentSubject.value && subjects.length > 0) {
    currentSubject.value = subjects[0]
  }
}
</script>

<template>
  <div>
    <select v-model="currentSubject">
      <option v-for="subject in allSubjects" :key="subject" :value="subject">
        {{ subject }}
      </option>
    </select>

    <PollComponent
      :subject="currentSubject"
      @subjectAdded="handleSubjectAdded"
      @subjectsUpdated="handleSubjectsUpdated"
    />
  </div>
</template>
