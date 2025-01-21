import * as React from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import NextLink from 'next/link';
import ProTip from '@/components/ProTip';
import Copyright from '@/components/Copyright';
import UploadPdf from '@/components/UploadPdf';

export default function Home() {
  return (
    <Container maxWidth="lg">
      <Box>
        <UploadPdf />
      </Box>
    </Container>
  );
}
