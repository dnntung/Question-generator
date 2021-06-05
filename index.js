const {exec} = require('child_process')
const express = require('express')
const app = express()

app.use(express.urlencoded({extended: false}))
app.set('view engine', 'ejs')

app.get('/', (req,res) => {
  return res.render('index')
})

app.get('/convert', (req,res) => {
  const {query} = req.query
  const conda_exec = "C:\\ProgramData\\Anaconda3\\Scripts\\conda.exe"
  const env_name = "py36"
  const file_exec = 'script1.py'
  const sub_cmd = ['python', file_exec, query].join(' ')
  
  const command = [conda_exec, 'run', '-n', env_name, sub_cmd].join(' ')
  
  exec(command,
      function(error, stdout, stderr){
          return res.json({
            error, 
            stdout: stdout.replace(/\n/g,''), 
            stderr
          })
      }
  );
})

app.listen(8080, () => console.log('Online'))

